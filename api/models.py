from typing import Optional, Dict, Any
from pydantic import BaseModel


# Модель для фильтров (можно вынести в отдельный файл)
class InternshipFilters(BaseModel):
    profession: Optional[str] = None
    company_name: Optional[str] = None
    salary_from: Optional[int] = None
    salary_to: Optional[int] = None
    source_name: Optional[str] = None
    employment_type: Optional[str] = None
    description: Optional[str] = None


class InternshipKeywords(BaseModel):
    keywords: str
    salary_from: Optional[int] = None
    salary_to: Optional[int] = None
    employment_type: Optional[str] = None


def get_clean_filters(self) -> Dict[str, Any]:
    filters = {}
    for key, value in self.__dict__.items():
        if value is not None:
            if isinstance(value, (int, float)):
                value = str(value)
            filters[key] = value.split(",")
    return filters
