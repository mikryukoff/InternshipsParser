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
            LEXICON_COMMANDS["no_salary"],
            LEXICON_COMMANDS["up_to_1_month"],
            LEXICON_COMMANDS["1_to_3_months"],
            LEXICON_COMMANDS["3_months_or_more"],
            LEXICON_COMMANDS["all_durations"]
        ]

    async def __call__(self, message: Message) -> bool:
        return message.text in self.options


class SalaryFilter(BaseFilter):
    "Класс, описывающий фильтр для отслеживания введенного диапазона зарплаты"
    async def __call__(self, message: Message) -> bool:
        match = re.match(r'^\s*(\d+)\s*[-–—]\s*(\d+)\s*$', message.text)
        return bool(match)
