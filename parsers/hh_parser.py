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
        try:
            async with session.get(f"{self.url}/{vacancy_id}") as response:
                if response.status == 200:
                    return await response.json()
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
                            break

                        data = await response.json()
                        vacancies = data.get('items', [])

                        # Обработка вакансий асинхронно
                        tasks = []
                        for item in vacancies:
                            tasks.append(self.process_vacancy(
                                session, item, internships_table))

                        await asyncio.gather(*tasks)

                        # Проверка последней страницы
                        if page >= data['pages'] - 1:
                            break
                        page += 1

                except Exception as e:
                    logger.error(f"Ошибка при запросе: {str(e)}")
                    break

    async def process_vacancy(self, session: aiohttp.ClientSession, item: dict, internships_table: Internships):
        """Обработка и сохранение одной вакансии"""
        try:
            vacancy_data = await self.fetch_vacancy_details(session, item['id'])
            if not vacancy_data:
                return

            salary = vacancy_data.get('salary', {})
            professional_roles = vacancy_data.get('professional_roles', [{}])
            employer = vacancy_data.get('employer', {})
            description = vacancy_data.get('description', '')
            if description:
                description = re.sub(r'(?:<).*?(?:>)', '', description).replace("\n", " ").strip()

            await internships_table.insert_internship(
                title=vacancy_data.get('name', ''),
                profession=professional_roles[0].get('name', ''),
                company_name=employer.get('name', ''),
                salary_from=salary.get('from'),
                salary_to=salary.get('to', 1.0),
                duration=None,
                employment=vacancy_data.get('employment', {}).get('name', ''),
                source_name=self.source_name,
                link=vacancy_data.get('alternate_url', ''),
                # Применяем очистку HTML
                description=description
            )

        except Exception as e:
            logger.error(
                f"Ошибка обработки вакансии {item.get('id')}: {str(e)}")


if __name__ == "__main__":
    parser = HHParser()
    asyncio.run(parser.get_internships())
