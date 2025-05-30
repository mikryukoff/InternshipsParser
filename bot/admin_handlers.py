import asyncio

from aiogram import Router, F
from aiogram.types import Message

from bot.lexicon import LEXICON, LEXICON_COMMANDS
import bot.menu_kb as kb
from bot.menu_handlers import add_to_history
from common import TrudVsemParser, HHParser
from common.logger import get_logger
from common.database import initialize_databases, Internships


# Инициализация роутера
router: Router = Router()

# Инициализация логгера
logger = get_logger(__name__)


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
    tables = await initialize_databases()
    internships_table: Internships = tables[1]

    trudvsem_parser: TrudVsemParser = TrudVsemParser()
    hh_parser: HHParser = HHParser()

    await message.answer(text=LEXICON["processing"])
    logger.info("Updating DB")
    try:
        await asyncio.gather(
            trudvsem_parser.get_internships(),
            hh_parser.get_internships()
        )
        await internships_table.update_internships()
        await message.answer(text=LEXICON["db_succeed_update"])
    except Exception as e:
        logger.error(str(e))
        await message.answer(text=LEXICON["db_failed_update"])
