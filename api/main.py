from fastapi import FastAPI, HTTPException, Query, Response
from common.database import initialize_databases, Internships
from fastapi.responses import FileResponse
import tempfile
import json
from typing import Optional, Dict, Any

from common.logger import get_logger

app = FastAPI()

logger = get_logger(__name__)


# Модель для фильтров (можно вынести в отдельный файл)
class InternshipFilters:
    def __init__(
        self,
        profession: Optional[str] = None,
        company_name: Optional[str] = None,
        salary_from: Optional[int] = None,
        salary_to: Optional[int] = None,
        duration: Optional[str] = None,
        source_name: Optional[str] = None,
        employment_type: Optional[str] = None
    ):
        self.filters = {
            'profession': profession,
            'company_name': company_name,
            'salary_from': salary_from,
            'salary_to': salary_to,
            'duration': duration,
            'source_name': source_name,
            'employment_type': employment_type
        }

    def get_clean_filters(self) -> Dict[str, Any]:
        filters = {}
        for key, value in self.filters.items():
            if value is not None:
                if isinstance(value, (int, float)):
                    value = str(value)
                filters[key] = value.split(",")
        return filters


@app.get("/internships")
async def get_internships(
    response_format: Optional[str] = Query('json', description="Формат ответа: json или file"),
    profession: Optional[str] = Query(None, description="Фильтр по профессии"),
    company_name: Optional[str] = Query(None, description="Фильтр по названию компании"),
    salary_from: Optional[int] = Query(None, description="Минимальная зарплата"),
    salary_to: Optional[int] = Query(None, description="Максимальная зарплата"),
    duration: Optional[str] = Query(None, description="Длительность стажировки"),
    source_name: Optional[str] = Query(None, description="Название источника"),
    employment_type: Optional[str] = Query(None, description="Тип занятости")
):
    try:
        # Собираем фильтры
        filters = InternshipFilters(
            profession=profession,
            company_name=company_name,
            salary_from=salary_from,
            salary_to=salary_to,
            duration=duration,
            source_name=source_name,
            employment_type=employment_type
        ).get_clean_filters()

        logger.info(filters)

        # Получаем данные
        tables = await initialize_databases()
        internships_table: Internships = tables[1]
        result = await internships_table.select_internship_data(**filters)

        # Формируем данные
        headers = [
            'id', 'title', 'profession', 'company_name', 'salary_from',
            'salary_to', 'duration', 'source_name', 'link',
            'description', 'created_at', 'updated_at', 'employment_types'
        ]

        data = []
        for row in result:
            item = {
                header: str(value) if value is not None else ''
                for header, value in zip(headers, row)
            }
            # Конвертация числовых полей
            for numeric_field in ['id', 'salary_from', 'salary_to']:
                if item[numeric_field].isdigit():
                    item[numeric_field] = int(item[numeric_field])

            data.append(item)

        # Возвращаем в нужном формате
        if response_format == 'file':
            with tempfile.NamedTemporaryFile(
                mode='w',
                suffix='.json',
                delete=False,
                encoding='utf-8'
            ) as tmpfile:
                json.dump(data, tmpfile, ensure_ascii=False, indent=4)
                tmpfile_path = tmpfile.name

            return FileResponse(
                tmpfile_path,
                filename="internships.json",
                media_type='application/json'
            )
        else:
            return data

    except Exception as e:
        raise HTTPException(500, detail=str(e))
