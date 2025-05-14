from aiogram import Router, F
from aiogram.types import Message

from bot.lexicon import LEXICON, LEXICON_COMMANDS
import bot.menu_kb as kb
from bot.filters import AnswerFilter, SalaryFilter, ProfessionFilter
from bot.menu_handlers import add_to_history, add_to_query, remove_from_query
from common.database import initialize_databases, EmploymentTypes
from bot.menu_kb import employment_types_keyboard, sites_keyboard

from aiogram.fsm.state import StatesGroup, State
from aiogram.fsm.context import FSMContext
from aiogram.fsm.storage.memory import MemoryStorage


employment_types = []
professions = {}

# Инициализация роутера
router: Router = Router()

storage = MemoryStorage()


class FilterState(StatesGroup):
    ACTIVE_FILTERS = State()  # Единое состояние для всех фильтров


# Обработка кнопки "Фильтры", переход на выбор сайтов
@router.message(F.text == LEXICON_COMMANDS["filters"])
async def select_site(message: Message, state: FSMContext):
    await state.set_state(FilterState.ACTIVE_FILTERS)
    await state.update_data(filters={})
    user_id = message.from_user.id
    add_to_history(user_id, "sites_menu")
    await message.answer(LEXICON["select_site"], reply_markup=sites_keyboard())


# Обработка выбора конкретного сайта
@router.message(lambda message: any(
    site in message.text.replace("✅", "")
    for site in LEXICON_COMMANDS["sites"]
))
async def toggle_site(message: Message, state: FSMContext):
    data = await state.get_data()
    selected = data.get("filters", {}).get("source_name", [])
    site = message.text.replace("✅", "")

    if site in selected:
        await remove_from_query(state, source_name=site)
        selected.remove(site)
    else:
        await add_to_query(state, source_name=site)
        selected.append(site)

    await message.answer(
        text=f"Сайт {site} {'выбран' if site in selected else 'удален из выбора'}",
        reply_markup=sites_keyboard(selected=selected)
    )


# Обработка кнопки "Все сайты"
@router.message(F.text == LEXICON_COMMANDS["all_sites"])
async def select_all_sites(message: Message, state: FSMContext):
    data = await state.get_data()
    selected = set(data.get("filters", {}).get("source_name", []))

    all_sites = set(LEXICON_COMMANDS["sites"])

    if selected == all_sites:
        await remove_from_query(state, source_name=LEXICON_COMMANDS["sites"])
        await message.answer(
            text="Все сайты сняты с выбора",
            reply_markup=sites_keyboard()
        )
    else:
        await add_to_query(state, source_name=LEXICON_COMMANDS["sites"])
        await message.answer(
            text="Все сайты выбраны",
            reply_markup=sites_keyboard(selected=all_sites)
        )


# Обработка фильтра по профессии
@router.message(F.text == LEXICON_COMMANDS["profession"])
async def select_profession(message: Message):
    user_id = message.from_user.id
    professions[user_id] = True

    add_to_history(user_id, "profession_menu")
    await message.answer(text=LEXICON["input_profession"])


@router.message(ProfessionFilter(professions))
async def process_profession_selection(message: Message, state: FSMContext):
    user_id = message.from_user.id
    professions[user_id] = False

    await add_to_query(state, profession=message.text)
    return message.answer(
        text=f'Профессии, включающие слова "{message.text}", добавлены'
    )


# Обработка меню занятости
@router.message(F.text == LEXICON_COMMANDS["employment"])
async def select_employment(message: Message, state: FSMContext):
    global employment_types
    user_id = message.from_user.id
    tables = await initialize_databases()
    employment_types_table: EmploymentTypes = tables[2]

    employment_types = await employment_types_table.select_employment_types()

    # Получаем текущие данные из состояния
    data = await state.get_data()
    selected = data.get("filters", {}).get("employment_type", [])

    add_to_history(user_id, "employment_menu")
    await message.answer(
        text=LEXICON["select_employment"],
        reply_markup=employment_types_keyboard(employment_types, selected)
    )


@router.message(lambda message: any(
    t in message.text.replace("✅", "")
    for t in employment_types
))
async def process_employment_selection(message: Message, state: FSMContext):
    employment_type = message.text.replace("✅", "").strip()

    # Получаем текущие данные из состояния
    data = await state.get_data()
    selected = data.get("filters", {}).get("employment_type", [])

    # Добавляем или удаляем тип (если уже выбран)
    if employment_type in selected:
        await remove_from_query(state, employment_type=employment_type)
        selected.remove(employment_type)
        await message.answer(
            text=f"Тип занятости {employment_type} удалён",
            reply_markup=employment_types_keyboard(employment_types, selected)
        )
    else:
        await add_to_query(state, employment_type=employment_type)
        selected.append(employment_type)
        await message.answer(
            text=f"Тип занятости {employment_type} выбран",
            reply_markup=employment_types_keyboard(employment_types, selected)
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


@router.message(F.text == LEXICON_COMMANDS["with_salary"])
async def process_salary_selection(message: Message):
    await message.answer(
        text=LEXICON["input_salary"]
    )


@router.message(SalaryFilter())
async def process_salary_input(message: Message, state: FSMContext):
    global salary
    salary = False

    salary_from, salary_to = map(str.strip, message.text.split("-"))

    await add_to_query(state, salary_from=salary_from)
    await add_to_query(state, salary_to=salary_to)

    await message.answer(
        text=f"Диапазон оклада {salary_from} - {salary_to} выбран",
        reply_markup=kb.FiltersMenu
    )


# Обработка выбора фильтров
@router.message(AnswerFilter())
async def filter_selected(message: Message):
    await message.answer(
        text=LEXICON["selected_option"].format(message.text),
        reply_markup=kb.FiltersMenu
    )
