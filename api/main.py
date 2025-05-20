from fastapi import FastAPI, HTTPException, Query
from common.database import initialize_databases, Internships
from fastapi.responses import FileResponse
import tempfile
import json
import asyncio
from typing import Optional

from common.logger import get_logger
from common import TrudVsemParser, HHParser

from api.models import InternshipFilters, InternshipKeywords, get_clean_filters


app = FastAPI()

logger = get_logger(__name__)


@app.get("/internships/filters")
async def get_internships(
    response_format: Optional[str] = Query('json', description="Формат ответа: json или file"),
    limit: int = Query(100, ge=1, le=1000, description="Количество записей на странице"),
    offset: int = Query(0, ge=0, description="Смещение (пропуск записей)"),

    profession: Optional[str] = Query(None, description="Фильтр по профессии"),
    company_name: Optional[str] = Query(None, description="Фильтр по названию компании"),
    salary_from: Optional[int] = Query(None, description="Минимальная зарплата"),
    salary_to: Optional[int] = Query(None, description="Максимальная зарплата"),
    source_name: Optional[str] = Query(None, description="Название источника"),
    employment_type: Optional[str] = Query(None, description="Тип занятости"),
    description: Optional[str] = Query(None, description="Описание стажировки")
):
    try:
        # Собираем фильтры
        filters = get_clean_filters(
            InternshipFilters(
                profession=profession,
                company_name=company_name,
                salary_from=salary_from,
                salary_to=salary_to,
                source_name=source_name,
                employment_type=employment_type,
                description=description
            )
        )

        logger.info(filters)

        return await build_response(
            response_format=response_format,
            filters=filters,
            limit=limit,
            offset=offset
        )

    except Exception as e:
        raise HTTPException(500, detail=str(e))


@app.get("/internships/keywords")
async def get_internships_by_keywords(
    response_format: Optional[str] = Query('json', description="Формат ответа: json или file"),
    limit: int = Query(100, ge=1, le=1000, description="Количество записей на странице"),
    offset: int = Query(0, ge=0, description="Смещение (пропуск записей)"),

    keywords: str = Query(description="Перечислите ключевые слова через запятую, перед словами-исключениями поставьте '-' (например, 'python, -java')"),
    salary_from: Optional[int] = Query(None, description="Минимальная зарплата"),
    salary_to: Optional[int] = Query(None, description="Максимальная зарплата"),
    employment_type: Optional[str] = Query(None, description="Тип занятости")
):
    try:
        filters = get_clean_filters(
            InternshipKeywords(
                keywords=keywords,
                salary_from=salary_from,
                salary_to=salary_to,
                employment_type=employment_type
            )
        )
        logger.info(filters)

        return await build_response(
            response_format=response_format,
            filters=filters,
            limit=limit,
            offset=offset
        )

    except Exception as e:
        raise HTTPException(500, detail=str(e))


async def build_response(
    response_format: str,
    filters: dict,
    limit: int,
    offset: int
):
    tables = await initialize_databases()
    internships_table: Internships = tables[1]
    if filters.get("keywords", None):
        result = await internships_table.select_internship_data_by_keywords(**filters)
    else:
        result = await internships_table.select_internship_data(**filters)

    # Формируем данные
    headers = [
        'id', 'title', 'profession', 'company_name', 'salary_from',
        'salary_to', 'source_name', 'link',
        'description', 'created_at', 'employment_types'
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

    total = len(data)

    response_data = {
        "data": data,
        "pagination": {
            "total": total,
            "limit": limit,
            "offset": offset,
            "has_more": (offset + limit) < total
        }
    }

    # Возвращаем в нужном формате
    if response_format == 'file':
        with tempfile.NamedTemporaryFile(
            mode='w',
            suffix='.json',
            delete=False,
            encoding='utf-8'
        ) as tmpfile:
            json.dump(response_data, tmpfile, ensure_ascii=False, indent=4)
            tmpfile_path = tmpfile.name

        return FileResponse(
            tmpfile_path,
            filename="internships.json",
            media_type='application/json'
        )
    else:
        return response_data


@app.put("/internships/update_db")
async def update_db():
    trudvsem_parser = TrudVsemParser()
    hh_parser = HHParser()
    logger.info("Updating DB")
    try:
        await asyncio.gather(
            trudvsem_parser.get_internships(),
            hh_parser.get_internships()
        )
        return {"status": "success", "updated": True}
    except Exception as e:
        logger.error(f"Update failed: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Database update failed: {str(e)}"
        )
