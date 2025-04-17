from dataclasses import dataclass
import requests
import asyncio


@dataclass
class TrudVsemParser:
    url: str = "http://opendata.trudvsem.ru/api/v1/vacancies/"

    async def get_some_info(self):
        response = (requests.get(f"{self.url}region/6600000000000?text=стажер"))
        data = response.json()["results"]["vacancies"]

        for i in data:
            vacancy = i["vacancy"]
            profession = vacancy["job-name"]
            company_name = vacancy["company"]["name"]
            salary_from = vacancy["salary_min"]
            salary_to = vacancy["salary_max"]
            link = vacancy["vac_url"]

            print(f"""
                Профессия: {profession}
                Название компании: {company_name}
                Зарплата: {salary_from} - {salary_to}
                Ссылка на вакансию: {link}
            """)


if __name__ == "__main__":
    parser = TrudVsemParser()
    asyncio.run(parser.get_some_info())
