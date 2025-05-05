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
        logger.debug(f"Загрузка деталей вакансии {vacancy_id}")
        try:
            async with session.get(f"{self.url}/{vacancy_id}") as response:
                if response.status == 200:
                    return await response.json()
                logger.warning(f"Ошибка {response.status} при загрузке вакансии {vacancy_id}")
                return None
        except Exception as e:
            logger.error(f"Error fetching vacancy {vacancy_id}: п{str(e)}")
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
                        if response.status != 200:
                            logger.error(f"Ошибка {response.status} при загрузке страницы {page}")
                            break
                        
                        data = await response.json()
                        vacancies = data.get('items', [])
                        logger.info(f"Найдено {len(vacancies)} вакансий на странице {page + 1}")

                        if not vacancies:
                            logger.info("Нет вакансий, завершение обработки")
                            break

                        # Обработка вакансий асинхронно
                        tasks = []
                        for item in vacancies:
                            tasks.append(self.process_vacancy(
                                session, item, internships_table))

                        await asyncio.gather(*tasks)
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

            salary = vacancy_data.get('salary', {})
            professional_roles = vacancy_data.get('professional_roles', [{}])
            employer = vacancy_data.get('employer', {})

            await internships_table.insert_internship(
                title=vacancy_data.get('name', ''),
                profession=professional_roles[0].get('name', ''),
                company_name=employer.get('name', ''),
                salary_from=salary.get('from'),
                salary_to=salary.get('to'),
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
