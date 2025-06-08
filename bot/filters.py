import re

from aiogram.filters import BaseFilter
from aiogram.types import Message

from bot.lexicon import LEXICON_COMMANDS
from common.logger import get_logger


logger = get_logger(__name__)


class AnswerFilter(BaseFilter):
    "Класс, описывающий фильтр для отслеживания нажатия по фильтрам."
    def __init__(self):
        self.options = [LEXICON_COMMANDS["no_salary"]]

    async def __call__(self, message: Message) -> bool:
        return message.text in self.options


class SalaryFilter(BaseFilter):
    "Класс, описывающий фильтр для отслеживания введенного диапазона зарплаты"
    def __init__(self, salary: dict):
        self.salary = salary

    async def __call__(self, message: Message) -> bool:
        match = re.match(r'^\s*(\d+)\s*[-–—]\s*(\d+)\s*$', message.text)
        return bool(match) and self.salary.get(message.from_user.id, False)


class ProfessionFilter(BaseFilter):
    "Класс, описывающий фильтр для отслеживания меню ввода профессии"
    def __init__(self, professions: dict):
        self.professions = professions

    async def __call__(self, message: Message) -> bool:
        return self.professions.get(message.from_user.id, False)


class EmploymentFilter(BaseFilter):
    "Класс, описывающий фильтр для отслеживания меню ввода типов занятости"
    def __init__(self, employment_types: dict):
        self.employment_types = employment_types

    async def __call__(self, message: Message) -> bool:
        return any(
            t == message.text.replace("✅", "") for t in self.employment_types
        )
