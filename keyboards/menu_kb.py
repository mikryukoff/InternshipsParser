# Импорты необходимых библиотек
from aiogram.types import ReplyKeyboardMarkup, KeyboardButton
from lexicon import LEXICON_COMMANDS

# Начальное меню
StartMenu = ReplyKeyboardMarkup(
    keyboard=[
        [
            KeyboardButton(text=LEXICON_COMMANDS["admin_panel"]),    # Кнопка "Админ-панель"
            KeyboardButton(text=LEXICON_COMMANDS["to_filters"])       # Кнопка "Фильтры"
        ]
    ],
    resize_keyboard=True,                       # Автоматическая настройка размера клавиатуры
    one_time_keyboard=True,                     # Клавиатура будет скрыта после использования
    input_field_placeholder="Начальное меню"    # Подсказка для поля ввода
)
