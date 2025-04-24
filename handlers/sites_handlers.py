from aiogram import Router, F
from aiogram.types import Message

from lexicon import LEXICON, LEXICON_COMMANDS
from keyboards import sites_keyboard
from handlers.menu_handlers import add_to_history, user_state, add_to_query, remove_from_query


# Инициализация роутера
router: Router = Router()


# Обработка кнопки "Фильтры", переход на выбор сайтов
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
        remove_from_query(user_id, source_name=site)
    else:
        selected.add(site)
        add_to_query(user_id, source_name=site)

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
        remove_from_query(user_id, source_name=LEXICON_COMMANDS["sites"])
        await message.answer("Все сайты сняты с выбора")
    else:
        user_state[user_id]["selected_sites"] = all_sites.copy()
        add_to_query(user_id, source_name=LEXICON_COMMANDS["sites"])
        await message.answer("Все сайты выбраны")
