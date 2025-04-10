# Импорты библиотек и модулей
from aiogram import Router
from aiogram.types import Message
from aiogram.filters import CommandStart

# Импорты пользовательских модулей
from lexicon import LEXICON

import keyboards.menu_kb as kb


# Инициализация роутера
router: Router = Router()


# Обработчик команды "/start"
@router.message(CommandStart())
async def process_start_command(message: Message) -> None:
    # Отправляем приветственное сообщение и показываем меню входа
    await message.answer(
        text=LEXICON["/start"],
        reply_markup=kb.StartMenu
    )
