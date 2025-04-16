from aiogram import Router, F
from aiogram.types import Message
from aiogram.filters import CommandStart
from typing import Dict, Any

from lexicon import LEXICON, LEXICON_COMMANDS
import keyboards.menu_kb as kb
from keyboards import sites_keyboard
from filters import AnswerFilter


# Инициализация роутера
router = Router()

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
    await message.answer(text=LEXICON["unvailable"])


# Обработка кнопки "Выгрузка файла"
@router.message(F.text == LEXICON_COMMANDS["export_file"])
async def export_file(message: Message):
    await message.answer(text=LEXICON["unvailable"])


# Обработка кнопки "Фильтры"
@router.message(F.text == LEXICON_COMMANDS["filters"])
async def select_site(message: Message):
    user_id = message.from_user.id
    add_to_history(user_id, "sites_menu")
    await message.answer(LEXICON["select_site"], reply_markup=sites_keyboard())


# Обработка выбора конкретного сайта
@router.message(F.text.in_(LEXICON_COMMANDS["sites"]))
async def toggle_site(message: Message):
    user_id = message.from_user.id
    if user_id not in user_state:
        user_state[user_id] = {"selected_sites": set()}
    
    site = message.text
    selected = user_state[user_id]["selected_sites"]
    
    if site in selected:
        selected.remove(site)
    else:
        selected.add(site)
    
    await message.answer(
        f"Сайт {site} {'выбран' if site in selected else 'удален из выбора'}"
    )


# Обработка кнопки "Все сайты"
@router.message(F.text == LEXICON_COMMANDS["all_sites"])
async def select_all_sites(message: Message):
    user_id = message.from_user.id
    if user_id not in user_state:
        user_state[user_id] = {"selected_sites": set()}
    
    all_sites = set(LEXICON_COMMANDS["sites"])
    
    if user_state[user_id]["selected_sites"] == all_sites:
        user_state[user_id]["selected_sites"] = set()
        await message.answer("Все сайты сняты с выбора")
    else:
        user_state[user_id]["selected_sites"] = all_sites.copy()
        await message.answer("Все сайты выбраны")


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