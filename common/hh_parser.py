from dataclasses import dataclass
import aiohttp
import asyncio
import re
import random
from typing import Optional, List
from aiohttp_socks import ProxyConnector
from aiohttp_retry import RetryClient, ExponentialRetry
from fake_useragent import UserAgent

from common.database import initialize_databases, Internships
from common.logger import get_logger


logger = get_logger(__name__)


def clean_html(text: str) -> str:
    """Очистка текста от HTML тегов"""
    return re.sub(r'<[^>]+>', '', text).replace("\n", " ").strip() if text else ""


@dataclass
class HHParser:
    url: str = "https://api.hh.ru/vacancies"
    source_name: str = "hh.ru"
    area_id: int = 3  # Екатеринбург
    per_page: int = 50
    proxy_urls: List[str] = None
    current_proxy_idx: int = -1

    def __post_init__(self):
        self.proxy_urls = self.proxy_urls or [
            'socks5://HK05WG:Y6WCNE@217.106.239.123:9980',
            'socks5://ynVLdR:ERfDaB@78.153.154.202:9883',
            'socks5://ynVLdR:ERfDaB@217.106.238.196:9096',
        ]
        random.shuffle(self.proxy_urls)
        self.current_proxy_idx = 0

    def get_next_proxy(self) -> str:
        """Получение следующего прокси с ротацией"""
        proxy = self.proxy_urls[self.current_proxy_idx]
        self.current_proxy_idx = (self.current_proxy_idx + 1) % len(self.proxy_urls)
        # logger.warning(f"Используется прокси: {proxy}")
        return proxy

    async def make_request(
        self,
        url: str,
        params: dict,
        headers: dict,
        retry_options: ExponentialRetry
    ) -> Optional[dict]:
        """Выполнение запроса с обработкой 403 и сменой прокси"""
        for attempt in range(len(self.proxy_urls)):
            proxy = self.get_next_proxy()
            try:
                connector = ProxyConnector.from_url(proxy)
                async with RetryClient(
                    connector=connector,
                    headers=headers,
                    retry_options=retry_options,
                    raise_for_status=False
                ) as session:
                    async with session.get(url, params=params) as response:
                        if response.status == 403:
                            raise PermissionError("403 Forbidden")
                        elif response.status >= 400:
                            raise aiohttp.ClientError(f"Ошибка {response.status}")
                        return await response.json()
            except (aiohttp.ClientError, PermissionError) as e:
                logger.warning(f"[{attempt+1}] Ошибка запроса через {proxy}: {e}")
                await asyncio.sleep(2)

        raise Exception("Все прокси недоступны или заблокированы (403)")

    async def get_internships(self):
        """Основной метод сбора данных"""
        tables = await initialize_databases()
        internships_table = tables[1]

        ua = UserAgent()
        headers = {'User-Agent': ua.random, 'Accept-Language': 'ru-RU,ru;q=0.9'}

        retry_options = ExponentialRetry(
            attempts=2,
            statuses=[429, 500, 502, 503, 504],
            exceptions=[asyncio.TimeoutError],
            max_timeout=20
        )

        page = 0
        while True:
            logger.info(f"Обработка страницы {page + 1}")
            params = {
                "text": "стажер OR стажировка OR internship",
                "area": self.area_id,
                "per_page": self.per_page,
                "page": page,
                "experience": 'noExperience'
            }

            try:
                data = await self.make_request(self.url, params, headers, retry_options)
                vacancies = data.get('items', [])
                if not vacancies:
                    logger.info("Нет вакансий, завершение.")
                    break

                logger.info(f"Найдено {len(vacancies)} вакансий")
                await self.process_vacancies(vacancies, internships_table, headers, retry_options)

                if page >= data.get('pages', 0) - 1:
                    logger.info("Последняя страница достигнута.")
                    break

                page += 1
            except Exception as e:
                logger.error(f"Критическая ошибка: {e}")
                break

        logger.info("Сбор стажировок с HH завершен.")

    async def process_vacancies(
        self,
        vacancies: list,
        internships_table: Internships,
        headers,
        retry_options
    ):
        batch_size = 10
        delay = 1.2

        for i in range(0, len(vacancies), batch_size):
            batch = vacancies[i:i+batch_size]
            tasks = [self.process_vacancy(item, internships_table, headers, retry_options) for item in batch]
            await asyncio.gather(*tasks)
            if i + batch_size < len(vacancies):
                await asyncio.sleep(delay)

    async def process_vacancy(
        self,
        item: dict,
        internships_table: Internships,
        headers,
        retry_options
    ):
        """Обработка и сохранение одной вакансии"""
        vacancy_id = item.get('id')
        for attempt in range(len(self.proxy_urls)):
            proxy = self.get_next_proxy()
            try:
                connector = ProxyConnector.from_url(proxy)
                async with RetryClient(
                    connector=connector,
                    headers=headers,
                    retry_options=retry_options,
                    raise_for_status=False
                ) as session:
                    async with session.get(f"{self.url}/{vacancy_id}") as response:
                        if response.status >= 400:
                            raise aiohttp.ClientError(f"Ошибка {response.status}")
                        vacancy_data = await response.json()

                        if not vacancy_data:
                            return

                        salary = vacancy_data.get('salary') or {}
                        professional_roles = vacancy_data.get('professional_roles', [{}])
                        employer = vacancy_data.get('employer', {})

                        salary_from = salary.get('from', 0) or 0
                        salary_to = salary.get('to', 0) or 0

                        await internships_table.insert_internship(
                            title=vacancy_data.get('name', ''),
                            profession=professional_roles[0].get('name', ''),
                            company_name=employer.get('name', ''),
                            salary_from=float(salary_from),
                            salary_to=float(salary_to),
                            employment=vacancy_data.get('employment', {}).get('name', ''),
                            source_name=self.source_name,
                            link=vacancy_data.get('alternate_url', ''),
                            description=clean_html(vacancy_data.get('description', '')))

                        logger.info(f"Успешно обработана вакансия [{vacancy_id}] \"{vacancy_data.get('name', '')}\" через {proxy}")
                        return
            except Exception as e:
                logger.warning(f"Ошибка обработки вакансии {vacancy_id} через {proxy}: {e}")
                await asyncio.sleep(1)

        logger.error(f"Не удалось обработать вакансию {vacancy_id} — все прокси недоступны.")


if __name__ == "__main__":
    parser = HHParser()
    asyncio.run(parser.get_internships())
