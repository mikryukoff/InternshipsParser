from dataclasses import dataclass
import requests
import asyncio

from database import initialize_databases, Sources, Internships


@dataclass
class TrudVsemParser:
    url: str = "http://opendata.trudvsem.ru/api/v1/vacancies/"
    source_name: str = "trudvsem.ru"

    async def get_some_info(self):
        tables = await initialize_databases()
        _, internships_table = tables
        response = (requests.get(f"{self.url}region/6600000000000?text=стажер"))
        data = response.json()["results"]["vacancies"]

        for i in data:
            vacancy = i["vacancy"]
            title = vacancy["job-name"]
            profession = vacancy["job-name"]
            company_name = vacancy["company"]["name"]
            salary_from = vacancy["salary_min"]
            salary_to = vacancy["salary_max"]
            employment = vacancy.get("employment", "Нет данных")
            link = vacancy["vac_url"]
            description = vacancy["duty"]

            await internships_table.insert_internship(
                title=title,
                profession=profession,
                company_name=company_name,
                salary_from=salary_from,
                salary_to=salary_to,
                duration=None,
                employment=employment,
                source_name=self.source_name,
                link=link,
                description=description
            )


if __name__ == "__main__":
    parser = TrudVsemParser()
    asyncio.run(parser.get_some_info())
