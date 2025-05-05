from dataclasses import dataclass
import aiohttp
import asyncio
import re
from typing import Optional

from database import initialize_databases, Internships
from logger import get_logger


# Инициализация логгера
logger = get_logger(__name__)


def clean_html(text: str) -> str:
    """Очистка текста от HTML тегов"""
    if not text:
        return ""
    return re.sub(r'<[^>]+>', '', text).replace("\n", " ").strip()


@dataclass
class HHParser:
    url: str = "https://api.hh.ru/vacancies"
    source_name: str = "hh.ru"
    area_id: int = 3  # Екатеринбург
    per_page: int = 50

    async def fetch_vacancy_details(self, session: aiohttp.ClientSession, vacancy_id: str) -> Optional[dict]:
        """Асинхронное получение деталей вакансии"""

        max_retries = 3
        base_delay = 0.3

        for attempt in range(max_retries):
            try:
                async with session.get(f"{self.url}/{vacancy_id}") as response:
                    if response.status == 200:
                        logger.info(f"Успешно загружена вакансия {vacancy_id} (попытка {attempt + 1})")
                        return await response.json()
                    elif response.status == 403:
                        delay = base_delay * (attempt + 1)
                        logger.warning(f"403 Ошибка для вакансии {vacancy_id }(попытка {attempt + 1}). Пауза {delay} сек")
                        await asyncio.sleep(delay)
                        continue
                    else:
                        logger.warning(f"Ошибка {response.status} при загрузке вакансии {vacancy_id}")
                        return None
            except Exception as e:
                logger.error(f"Ошибка получения вакансии {vacancy_id}: {str(e)}")
                await asyncio.sleep(base_delay)
    
        logger.error(f"Не удалось загрузить вакансию {vacancy_id} после {max_retries} попыток")
        return None

    async def get_internships(self):
        """Основной метод для получения и сохранения стажировок"""
        tables = await initialize_databases()
        internships_table = tables[1]

        async with aiohttp.ClientSession() as session:
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
                    async with session.get(self.url, params=params) as response:
                        if response.status == 403:
                            logger.warning("Получена ошибка 403 при загрузке страницы. Делаю паузу 2 секунды...")
                            await asyncio.sleep(0.3)
                            continue
                        
                        await asyncio.sleep(3)

                        if response.status != 200:
                            logger.error(f"Ошибка {response.status} при загрузке страницы {page}")
                            break
                        
                        data = await response.json()
                        vacancies = data.get('items', [])
                        logger.info(f"Найдено {len(vacancies)} вакансий на странице {page + 1}")

                        if not vacancies:
                            logger.info("Нет вакансий, завершение обработки")
                            break

                        # Обработка вакансий
                        batch_size = 4
                        delay = 1.1

                        for i in range(0, len(vacancies), batch_size):
                            batch = vacancies[i:i+batch_size]
                            tasks = [self.process_vacancy(session, item, internships_table) for item in batch]
                            await asyncio.gather(*tasks)
                            if i + batch_size < len(vacancies):
                                await asyncio.sleep(delay)

                        logger.info(f"Завершена обработка страницы {page + 1}")

                        # Проверка последней страницы
                        if page >= data['pages'] - 1:
                            logger.info("Достигнута последняя страница")
                            break
                        page += 1

                except Exception as e:
                    logger.error(f"Ошибка при запросе: {str(e)}")
                    break
        logger.info("Завершение сбора стажировок с HH")

    async def process_vacancy(self, session: aiohttp.ClientSession, item: dict, internships_table: Internships):
        """Обработка и сохранение одной вакансии"""
        try:
            vacancy_data = await self.fetch_vacancy_details(session, item['id'])
            if not vacancy_data:
                return

            salary = vacancy_data.get('salary') or {}
            professional_roles = vacancy_data.get('professional_roles', [{}])
            employer = vacancy_data.get('employer', {})

            salary_from = salary.get('from') if salary.get('from') is not None else 0
            salary_to = salary.get('to') if salary.get('to') is not None else 0

            await internships_table.insert_internship(
                title=vacancy_data.get('name', ''),
                profession=professional_roles[0].get('name', ''),
                company_name=employer.get('name', ''),
                salary_from=float(salary_from),
                salary_to=float(salary_to),
                duration=None,
                employment=vacancy_data.get('employment', {}).get('name', ''),
                source_name=self.source_name,
                link=vacancy_data.get('alternate_url', ''),
                # Применяем очистку HTML
                description=clean_html(vacancy_data.get('description', '')))

        except Exception as e:
            logger.error(f"Ошибка обработки вакансии {item.get('id')}: {str(e)}")


if __name__ == "__main__":
    parser = HHParser()
    asyncio.run(parser.get_internships())

