from aiogram import Router, F
from aiogram.types import Message

from lexicon import LEXICON, LEXICON_COMMANDS
import keyboards.menu_kb as kb
from handlers.menu_handlers import add_to_history
from parsers import TrudVsemParser


# Инициализация роутера
router: Router = Router()


# Обработка админ-панели
@router.message(F.text == LEXICON_COMMANDS["admin_panel"])
async def admin_panel(message: Message):
    user_id = message.from_user.id
    add_to_history(user_id, "admin_menu")
    await message.answer(LEXICON["admin_welcome"], reply_markup=kb.AdminMenu)


# Обработка кнопки "Добавить администратора"
@router.message(F.text == LEXICON_COMMANDS["add_admin"])
async def add_admin(message: Message):
    await message.answer(text=LEXICON["unvailable"])


# Обработка кнопки "Обновить БД"
@router.message(F.text == LEXICON_COMMANDS["update_db"])
async def update_db(message: Message):
    trudvsem_parser: TrudVsemParser = TrudVsemParser()
    try:
        await trudvsem_parser.get_some_info()
        await message.answer(text=LEXICON["db_succeed_update"])
    except Exception:
        await message.answer(text=LEXICON["db_failed_update"])
