from aiogram import Router, F
from aiogram.types import Message

from lexicon import LEXICON, LEXICON_COMMANDS
import keyboards.menu_kb as kb
from filters import AnswerFilter
from handlers.menu_handlers import add_to_history


# Инициализация роутера
router: Router = Router()


# Обработка фильтра по профессии
@router.message(F.text == LEXICON_COMMANDS["profession"])
async def select_profession(message: Message):
    await message.answer(text=LEXICON["unvailable"])


# Обработка меню занятости
@router.message(F.text == LEXICON_COMMANDS["employment"])
async def select_employment(message: Message):
    user_id = message.from_user.id
    add_to_history(user_id, "employment_menu")
    await message.answer(
        text=LEXICON["select_employment"],
        reply_markup=kb.EmploymentMenu
    )


# Обработка меню оклада
@router.message(F.text == LEXICON_COMMANDS["salary"])
async def select_salary(message: Message):
    user_id = message.from_user.id
    add_to_history(user_id, "salary_menu")
    await message.answer(
        text=LEXICON["select_salary"],
        reply_markup=kb.SalaryMenu
    )


# Обработка меню длительности
@router.message(F.text == LEXICON_COMMANDS["duration"])
async def select_duration(message: Message):
    user_id = message.from_user.id
    add_to_history(user_id, "duration_menu")
    await message.answer(
        text=LEXICON["select_duration"],
        reply_markup=kb.DurationMenu
    )


# Обработка выбора фильтров
@router.message(AnswerFilter())
async def filter_selected(message: Message):
    await message.answer(
        text=LEXICON["selected_option"].format(message.text),
        reply_markup=kb.FiltersMenu
    )
