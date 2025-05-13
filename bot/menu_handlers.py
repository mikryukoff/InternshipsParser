import json
import tempfile
import os

from aiogram.types import FSInputFile
from aiogram import Router, F
from aiogram.types import Message
from aiogram.filters import CommandStart
from aiogram.fsm.context import FSMContext
from typing import Any

from bot.lexicon import LEXICON, LEXICON_COMMANDS
import bot.menu_kb as kb
from bot.menu_kb import sites_keyboard, employment_types_keyboard

from common.database import initialize_databases, Sources, Internships, EmploymentTypes

from common.logger import get_logger


# Инициализация роутера
router: Router = Router()

logger = get_logger(__name__)

# Хранилища данных пользователей
user_history: dict[int, list] = dict()
user_state: dict[int, dict[str, Any]] = dict()
query: dict[int, dict[str, str | int | list]] = dict()


async def add_to_query(state: FSMContext, **kwargs):
    data = await state.get_data()
    current_filters = data.get("filters", {})

    for key, value in kwargs.items():
        if not isinstance(value, list):
            value = value.split(",")

        current = current_filters.get(key, [])
        current_filters[key] = list(set(current + value))

    await state.update_data(filters=current_filters)


async def remove_from_query(state: FSMContext, **kwargs):
    data = await state.get_data()
    current_filters = data.get("filters", {})

    for key, values in kwargs.items():
        if not isinstance(values, list):
            values = values.split(",")

        if key in current_filters:
            current_filters[key] = [v for v in current_filters[key] if v not in values]
            if not current_filters[key]:
                del current_filters[key]

    await state.update_data(filters=current_filters)


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
async def back_handler(message: Message, state: FSMContext):
    user_id = message.from_user.id
    previous_menu = get_previous_menu(user_id)

    # Получаем текущие данные из состояния
    data = await state.get_data()
    filters = data.get("filters", {})
    if filters:
        tables = await initialize_databases()
        employment_types_table: EmploymentTypes = tables[2]
        employment_types = await employment_types_table.select_employment_types()

        selected_sites = filters.get("source_name", [])
        selected_employments = filters.get("employment_type", [])

    if previous_menu:
        if previous_menu == "start":
            await message.answer(
                text=LEXICON["main_menu"],
                reply_markup=kb.StartMenu
            )

        elif previous_menu == "sites_menu":
            await message.answer(
                text=LEXICON["select_site"],
                reply_markup=sites_keyboard(selected_sites)
            )

        elif previous_menu == "filters_menu":
            await message.answer(
                text=LEXICON["select_filters"],
                reply_markup=kb.FiltersMenu
            )

        elif previous_menu == "employment_menu":
            await message.answer(
                text=LEXICON["select_employment"],
                reply_markup=employment_types_keyboard(
                    types=employment_types,
                    selected=selected_employments
                )
            )

        elif previous_menu == "salary_menu":
            await message.answer(
                text=LEXICON["select_salary"],
                reply_markup=kb.SalaryMenu
            )

        elif previous_menu == "duration_menu":
            await message.answer(
                text=LEXICON["select_duration"],
                reply_markup=kb.DurationMenu
            )

        elif previous_menu == "profession_menu":
            await message.answer(
                text=LEXICON["input_professioon"]
            )
    else:
        await message.answer("Главное меню", reply_markup=kb.StartMenu)
        user_history[user_id] = [kb.StartMenu]


# Обработка команды /start
@router.message(CommandStart())
async def cmd_start(message: Message):
    user_id = message.from_user.id
    add_to_history(user_id, "start")
    await message.answer(LEXICON["/start"], reply_markup=kb.StartMenu)


@router.message(F.text == LEXICON_COMMANDS["export_file"])
async def export_file(message: Message, state: FSMContext):
    tables = await initialize_databases()
    internships_table: Internships = tables[1]

    data = await state.get_data()
    filters = data.get("filters", {})
    result = await internships_table.select_internship_data(**filters)

    if not result:
        await message.answer("⚠️ Нет данных для экспорта")
        return

    # Создаем временный JSON-файл
    with tempfile.NamedTemporaryFile(
        mode='w',
        suffix='.json',
        delete=False,
        encoding='utf-8',
        newline=''
    ) as tmpfile:
        # Формируем структуру данных
        headers = [
            'id', 'title', 'profession', 'company_name', 'salary_from',
            'salary_to', 'duration', 'source_name', 'link',
            'description', 'created_at', 'updated_at', 'employment_types'
        ]

        json_data = []
        for row in result:
            item = {
                header: str(value) if value is not None else ''
                for header, value in zip(headers, row)
            }
            # Конвертация числовых полей
            for numeric_field in ['id', 'salary_from', 'salary_to']:
                if item[numeric_field].isdigit():
                    item[numeric_field] = int(item[numeric_field])

            json_data.append(item)

        # Записываем JSON с красивым форматированием
        json.dump(json_data, tmpfile, ensure_ascii=False, indent=4)
        tmpfile_path = tmpfile.name

    try:
        document = FSInputFile(
            path=tmpfile_path,
            filename='internships.json'
        )
        await message.answer_document(
            document=document,
            caption='📊 Результаты поиска стажировок',
            reply_markup=kb.StartMenu
        )
    finally:
        if tmpfile_path and os.path.exists(tmpfile_path):
            try:
                os.remove(tmpfile_path)
            except Exception as e:
                logger.error(f"Ошибка удаления файла: {e}")
        await state.clear()


# Обработка кнопки "Далее"
@router.message(F.text == LEXICON_COMMANDS["next"])
async def process_sites(message: Message):
    user_id = message.from_user.id

    add_to_history(user_id, "filters_menu")
    await message.answer(
        text="Выберите стажировки по доступным фильтрам.",
        reply_markup=kb.FiltersMenu
    )
