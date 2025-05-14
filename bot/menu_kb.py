from aiogram.types import ReplyKeyboardMarkup, KeyboardButton
from bot.lexicon import LEXICON_COMMANDS
from common.logger import get_logger


# Инициализация логгера
logger = get_logger(__name__)

# Главное меню
StartMenu = ReplyKeyboardMarkup(
    keyboard=[
        [
            KeyboardButton(text=LEXICON_COMMANDS["filters"]),
            KeyboardButton(text=LEXICON_COMMANDS["admin_panel"])
        ],
        [
            KeyboardButton(text=LEXICON_COMMANDS["export_file"])
        ]
    ],
    resize_keyboard=True,
    one_time_keyboard=True,
    input_field_placeholder="Выберите действие"
)

FiltersMenu = ReplyKeyboardMarkup(
    keyboard=[
        [
            KeyboardButton(text=LEXICON_COMMANDS["profession"])
        ],
        [
            KeyboardButton(text=LEXICON_COMMANDS["salary"])
        ],
        [
            KeyboardButton(text=LEXICON_COMMANDS["employment"])
        ],
        [
            KeyboardButton(text=LEXICON_COMMANDS["back"]),
            KeyboardButton(text=LEXICON_COMMANDS["export_file"])
        ]
    ],
    resize_keyboard=True,
    input_field_placeholder="Выберите фильтры"
)

AdminMenu = ReplyKeyboardMarkup(
    keyboard=[
        [
            KeyboardButton(text=LEXICON_COMMANDS["add_admin"]),
        ],
        [
            KeyboardButton(text=LEXICON_COMMANDS["update_db"])
        ],
        [
            KeyboardButton(text=LEXICON_COMMANDS["back"])
        ]
    ],
    resize_keyboard=True,
    input_field_placeholder="Администрирование"
)


SalaryMenu = ReplyKeyboardMarkup(
    keyboard=[
        [
            KeyboardButton(text=LEXICON_COMMANDS["no_salary"]),
            KeyboardButton(text=LEXICON_COMMANDS["with_salary"])
        ],
        [
            KeyboardButton(text=LEXICON_COMMANDS["back"]),
            KeyboardButton(text=LEXICON_COMMANDS["next"])
        ]
    ],
    resize_keyboard=True,
    input_field_placeholder="Выберите вариант оклада"
)


# Функция для генерации клавиатуры с сайтами
def sites_keyboard(selected: list[str] = None) -> ReplyKeyboardMarkup:
    "Функция, генерирующая клавиатуру со списком сайтов."
    if selected is None:
        selected = []
    keyboard = []
    row_count = len(LEXICON_COMMANDS["sites"]) // 2
    row_count += len(LEXICON_COMMANDS["sites"]) % 2

    step = 0
    for _ in range(row_count):
        if step + 2 <= len(LEXICON_COMMANDS["sites"]):
            row = []
            for j in range(step, step + 2):
                site = LEXICON_COMMANDS["sites"][j]
                text = f"✅{site}" if site in selected else site
                row.append(KeyboardButton(text=text))
        else:
            site = LEXICON_COMMANDS["sites"][-1]
            text = f"✅{site}" if site in selected else site
            row = [KeyboardButton(text=text)]
        keyboard.append(row)
        step += 2

    keyboard.append([KeyboardButton(text=LEXICON_COMMANDS["all_sites"])])
    keyboard.append([KeyboardButton(text=LEXICON_COMMANDS["back"]), KeyboardButton(text=LEXICON_COMMANDS["next"])])

    return ReplyKeyboardMarkup(
        keyboard=keyboard,                         # Клавиатура с кнопками
        resize_keyboard=True,                      # Автоматическая настройка размера клавиатуры
        one_time_keyboard=False,                   # Клавиатура не скрывается после использования
        input_field_placeholder="Список сайтов"    # Подсказка для поля ввода
    )


def employment_types_keyboard(types: tuple[str], selected: list[str] = None) -> ReplyKeyboardMarkup:
    if selected is None:
        selected = []
    keyboard = []

    for i in types:
        text = f"✅{i}" if i in selected else i
        keyboard.append([KeyboardButton(text=text)])

    keyboard.append([KeyboardButton(text=LEXICON_COMMANDS["back"]), KeyboardButton(text=LEXICON_COMMANDS["next"])])

    return ReplyKeyboardMarkup(
        keyboard=keyboard,                          # Клавиатура с кнопками
        resize_keyboard=True,                       # Автоматическая настройка размера клавиатуры
        one_time_keyboard=False,                    # Клавиатура не скрывается после использования
        input_field_placeholder="Типы занятости"    # Подсказка для поля ввода
    )
