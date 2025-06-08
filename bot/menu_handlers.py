import json
import tempfile
import os
import csv

from aiogram.types import FSInputFile
from aiogram import Router, F
from aiogram.types import Message
from aiogram.filters import CommandStart
from aiogram.fsm.context import FSMContext
from typing import Any

from bot.lexicon import LEXICON, LEXICON_COMMANDS
import bot.menu_kb as kb
from bot.menu_kb import sites_keyboard, employment_types_keyboard

from common.database import initialize_databases, Internships, EmploymentTypes

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
            current_filters[key] = [
                v for v in current_filters[key] if v not in values
            ]
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
    selected_sites = filters.get("source_name", [])

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
    else:
        await message.answer(
            text=LEXICON["main_menu"], reply_markup=kb.StartMenu
        )
        user_history[user_id] = [kb.StartMenu]


# Обработка команды /start
@router.message(CommandStart())
async def cmd_start(message: Message):
    user_id = message.from_user.id
    add_to_history(user_id, "start")
    await message.answer(LEXICON["/start"], reply_markup=kb.StartMenu)


@router.message(F.text == LEXICON_COMMANDS["export_file"])
async def export_file(message: Message):
    await message.answer(
        text=LEXICON["choose_file_type"],
        reply_markup=kb.ExportFileMenu
    )


def format_txt(data: list) -> str:
    """Форматирует данные в текстовый формат"""
    result = []
    for item in data:
        txt_entry = [
            f"ID: {item['id']}",
            f"Должность: {item['profession']}",
            f"Компания: {item['company_name']}",
            f"Зарплата: {item['salary_from']}-{item['salary_to']}",
            f"Источник: {item['source_name']}",
            f"Тип занятости: {item['employment_types']}",
            f"Ссылка: {item['link']}",
            f"Описание: {item['description']}",
            "-" * 40
        ]
        result.append("\n".join(txt_entry))
    return "\n\n".join(result)


def write_json(data: list, file_path: str):
    """Записывает данные в JSON файл"""
    with open(file_path, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=4)


def write_csv(data: list, file_path: str):
    """Записывает данные в CSV файл"""
    if not data:
        return

    fieldnames = data[0].keys()
    with open(file_path, 'w', encoding='utf-8', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(data)


def write_txt(data: list, file_path: str):
    """Записывает данные в TXT файл"""
    with open(file_path, 'w', encoding='utf-8') as f:
        f.write(format_txt(data))


@router.message(F.text.in_({"json", "csv", "txt"}))
async def process_export_file(message: Message, state: FSMContext):
    await message.answer(text=LEXICON["processing"])

    file_type = message.text
    file_ext = f".{file_type}"
    file_name = f"internships{file_ext}"

    try:
        # Получаем данные из состояния
        data = await state.get_data()
        filters = data.get("filters", {})

        # Получаем данные из БД
        tables = await initialize_databases()
        internships_table: Internships = tables[1]
        result = await internships_table.select_internship_data(**filters)

        if not result:
            await message.answer("⚠️ Нет данных для экспорта")
            await state.clear()
            return

        # Формируем структуру данных
        headers = [
            'id', 'title', 'profession', 'company_name', 'salary_from',
            'salary_to', 'source_name', 'link',
            'description', 'created_at', 'employment_types'
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

        # Создаем временный файл нужного формата
        with tempfile.NamedTemporaryFile(
            mode='w',
            suffix=file_ext,
            delete=False,
            encoding='utf-8',
            newline='' if file_type == 'csv' else None
        ) as tmpfile:
            tmpfile_path = tmpfile.name

        # Записываем данные в файл в зависимости от формата
        if file_type == "json":
            write_json(json_data, tmpfile_path)
        elif file_type == "csv":
            write_csv(json_data, tmpfile_path)
        elif file_type == "txt":
            write_txt(json_data, tmpfile_path)

        # Отправляем файл пользователю
        document = FSInputFile(
            path=tmpfile_path,
            filename=file_name
        )

        await message.answer_document(
            document=document,
            caption=f'📊 Результаты поиска стажировок ({file_type.upper()})',
            reply_markup=kb.StartMenu
        )

    except Exception as e:
        logger.error(f"Ошибка при экспорте файла: {e}")
        await message.answer(f"⚠️ Ошибка при создании файла: {e}")
    finally:
        # Удаляем временный файл
        if 'tmpfile_path' in locals() and os.path.exists(tmpfile_path):
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
        text=LEXICON["select_filters"],
        reply_markup=kb.FiltersMenu
    )
