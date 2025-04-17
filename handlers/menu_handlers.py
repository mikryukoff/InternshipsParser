from aiogram import Router, F
from aiogram.types import Message
from aiogram.filters import CommandStart
from typing import Dict, Any

from lexicon import LEXICON, LEXICON_COMMANDS
import keyboards.menu_kb as kb
from keyboards import sites_keyboard


# Инициализация роутера
router: Router = Router()

# Хранилища данных пользователей
user_history: Dict[int, list] = {}
user_state: Dict[int, Dict[str, Any]] = {}


# Добавление меню в историю переходов
def add_to_history(user_id: int, menu: Any):
    """Добавляем меню в историю переходов"""
    if user_id not in user_history:
        user_history[user_id] = []
    user_history[user_id].append(menu)


# Получение предыдущего меню
def get_previous_menu(user_id: int) -> Any:
    """Получаем предыдущее меню"""
    if user_id in user_history and len(user_history[user_id]) > 1:
        user_history[user_id].pop()  # Удаляем текущее меню
        return user_history[user_id][-1]  # Возвращаем предыдущее
    return None


# Обработка кнопки "Назад"
@router.message(F.text == LEXICON_COMMANDS["back"])
async def back_handler(message: Message):
    user_id = message.from_user.id
    previous_menu = get_previous_menu(user_id)

    if previous_menu:
        if previous_menu == "start":
            await message.answer("Главное меню", reply_markup=kb.StartMenu)
        elif previous_menu == "sites_menu":
            await message.answer("Выберите сайты:", reply_markup=sites_keyboard())
        elif previous_menu == "filters_menu":
            await message.answer("Выберите фильтры:", reply_markup=kb.FiltersMenu)
        elif previous_menu == "employment_menu":
            await message.answer("Выберите занятость:", reply_markup=kb.EmploymentMenu)
        elif previous_menu == "salary_menu":
            await message.answer("Выберите оклад:", reply_markup=kb.SalaryMenu)
        elif previous_menu == "duration_menu":
            await message.answer("Выберите длительность:", reply_markup=kb.DurationMenu)
    else:
        await message.answer("Главное меню", reply_markup=kb.StartMenu)
        user_history[user_id] = [kb.StartMenu]


# Обработка команды /start
@router.message(CommandStart())
async def cmd_start(message: Message):
    user_id = message.from_user.id
    add_to_history(user_id, "start")
    await message.answer(LEXICON["/start"], reply_markup=kb.StartMenu)


# Обработка кнопки "Выгрузка файла"
@router.message(F.text == LEXICON_COMMANDS["export_file"])
async def export_file(message: Message):
    await message.answer(text=LEXICON["unvailable"])


# Обработка кнопки "Далее"
@router.message(F.text == LEXICON_COMMANDS["next"])
async def process_sites(message: Message):
    user_id = message.from_user.id
    if user_id not in user_state or not user_state[user_id]["selected_sites"]:
        await message.answer("Пожалуйста, выберите хотя бы один сайт!")
        return

    add_to_history(user_id, "filters_menu")
    sites_list = "\n".join(f"• {site}" for site in user_state[user_id]["selected_sites"])
    await message.answer(
        f"Вы выбрали сайты:\n{sites_list}\n\n{LEXICON['select_filters']}",
        reply_markup=kb.FiltersMenu
    )
