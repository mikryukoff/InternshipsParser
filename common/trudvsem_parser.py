from dataclasses import dataclass
import aiohttp
import asyncio
from typing import Optional

from common.database import initialize_databases, Sources, Internships
from common.logger import get_logger

logger = get_logger(__name__)

@dataclass
class TrudVsemParser:
    url: str = "http://opendata.trudvsem.ru/api/v1/vacancies/region/6600000000000" # 6600000000000 - Екатеринбург
    source_name: str = "trudvsem.ru"
    per_page: int = 100
    base_delay: float = 1.2

    async def fetch_vacancies(self, session: aiohttp.ClientSession, page: int) -> Optional[dict]:
        """Получение списка вакансий с обработкой ошибок"""
        params = {
            "text": "стажировка",
            "offset": page * self.per_page,
            "limit": self.per_page
        }

        for attempt in range(3):
            try:
                async with session.get(
                    self.url,
                    params=params,
                    timeout=aiohttp.ClientTimeout(total=10)
                ) as response:
                    
                    if response.status == 200:
                        logger.info(f"Успешно загружена страница {page+1}")
                        return await response.json()
                    
                    logger.warning(
                        f"Ошибка {response.status} при загрузке страницы {page+1} "
                        f"(попытка {attempt+1}/3)"
                    )
                    await asyncio.sleep(self.base_delay * (attempt + 1))

            except Exception as e:
                logger.error(f"Ошибка подключения: {str(e)}")
                await asyncio.sleep(self.base_delay * 2)
        
        logger.error(f"Не удалось загрузить страницу {page+1} после 3 попыток")
        return None

    async def process_vacancy(self, vacancy: dict, internships_table: Internships):
        """Обработка и сохранение вакансии"""
        try:
            vacancy_data = vacancy.get("vacancy", {})
            company_data = vacancy_data.get("company", {})

            # Извлечение данных
            title = vacancy_data.get("job-name", "")
            company = company_data.get("name", "")
            link = vacancy_data.get("vac_url", "")
            
            salary_from = vacancy_data.get("salary_min", 0) or 0
            salary_to = vacancy_data.get("salary_max", 0) or 0

            await internships_table.insert_internship(
                title=title,
                profession=title,
                company_name=company,
                salary_from=float(salary_from),
                salary_to=float(salary_to),
                employment=vacancy_data.get("employment", ""),
                source_name=self.source_name,
                link=link,
                description=vacancy_data.get("duty", "")
            )

            logger.info(f"Успешно обработана вакансия: {title[:50]}...")

        except KeyError as e:
            logger.error(f"Отсутствует обязательное поле: {str(e)}")
        except ValueError as e:
            logger.error(f"Ошибка преобразования данных: {str(e)}")
        except Exception as e:
            logger.error(f"Ошибка обработки вакансии: {str(e)}")

    async def get_internships(self):
        """Основной метод сбора данных"""
        tables = await initialize_databases()
        internships_table = tables[1]

        async with aiohttp.ClientSession() as session:
            page = 0
            while True:
                logger.info(f"Обработка страницы {page + 1}")
                
                data = await self.fetch_vacancies(session, page)
                if not data:
                    break

                results = data.get("results", {})
                vacancies = results.get("vacancies", [])
                total = results.get("total", 0)
                
                logger.info(f"Найдено {len(vacancies)} вакансий на странице {page + 1}")

                # Обработка с вакансий
                batch_size = 5
                for i in range(0, len(vacancies), batch_size):
                    batch = vacancies[i:i+batch_size]
                    tasks = [self.process_vacancy(v, internships_table) for v in batch]
                    await asyncio.gather(*tasks)
                    
                    if i + batch_size < len(vacancies):
                        await asyncio.sleep(self.base_delay)

                # Проверка пагинации
                if (page + 1) * self.per_page >= total:
                    logger.info("Достигнута последняя страница")
                    break
                
                page += 1

            logger.info("Завершение сбора стажировок с TrudVsem")

if __name__ == "__main__":
    parser = TrudVsemParser()
    asyncio.run(parser.get_internships())