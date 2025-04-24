from aiogram import Router, F
from aiogram.types import Message
from aiogram.filters import CommandStart
from typing import Any

from lexicon import LEXICON, LEXICON_COMMANDS
import keyboards.menu_kb as kb
from keyboards import sites_keyboard

from database import initialize_databases, Sources, Internships

# Инициализация роутера
router: Router = Router()

# Хранилища данных пользователей
user_history: dict[int, list] = dict()
user_state: dict[int, dict[str, Any]] = dict()
query: dict[int, dict[str, str | int | list]] = dict()


def add_to_query(user_id: int, **kwargs):
    user_query = query.setdefault(user_id, {})

    for key, value in kwargs.items():
        if not isinstance(value, list):
            value = [value]

        current = user_query.get(key, [])
        if not isinstance(current, list):
            current = [current]

        new_values = [v for v in value if v not in current]
        user_query[key] = current + new_values

    query[user_id] = user_query


def remove_from_query(user_id: int, **kwargs):
    if user_id not in query:
        return

    user_query = query[user_id]

    for key, values in kwargs.items():
        if key not in user_query:
            continue

        if not isinstance(values, list):
            values = [values]

        if isinstance(user_query[key], list):
            user_query[key] = [item for item in user_query[key] if item not in values]

            if not user_query[key]:
                del user_query[key]
        else:
            if user_query[key] in values:
                del user_query[key]

    query[user_id] = user_query


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
    user_id = message.from_user.id
    tables = await initialize_databases()
    _, internships_table = tables
    internships_table: Internships = internships_table
    if user_id in query:
        result = await internships_table.select_internship_data(**query[user_id])
    else:
        result = await internships_table.select_internship_data()
    for i in range(10):
        await message.answer(text=" ".join([str(j) for j in result[i]]))


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
