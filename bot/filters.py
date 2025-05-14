import re

from aiogram.filters import BaseFilter
from aiogram.types import Message

from bot.lexicon import LEXICON_COMMANDS
from common.logger import get_logger


logger = get_logger(__name__)


class AnswerFilter(BaseFilter):
    "Класс, описывающий фильтр для отслеживания нажатия по фильтрам."
    def __init__(self):
        self.options = [
            LEXICON_COMMANDS["full_time"],
            LEXICON_COMMANDS["part_time"],
            LEXICON_COMMANDS["remote_employment"],
            LEXICON_COMMANDS["all_employment"],
            LEXICON_COMMANDS["no_salary"]
        ]

    async def __call__(self, message: Message) -> bool:
        return message.text in self.options


class SalaryFilter(BaseFilter):
    "Класс, описывающий фильтр для отслеживания введенного диапазона зарплаты"
    async def __call__(self, message: Message) -> bool:
        match = re.match(r'^\s*(\d+)\s*[-–—]\s*(\d+)\s*$', message.text)
        return bool(match)


class ProfessionFilter(BaseFilter):
    "Класс, описывающий фильтр для отслеживания меню ввода профессии"
    def __init__(self, professions: dict):
        self.professions = professions

    async def __call__(self, message: Message) -> bool:
        return self.professions.get(message.from_user.id, False)
