from aiogram.types import ReplyKeyboardMarkup, KeyboardButton
from lexicon import LEXICON_COMMANDS

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
            KeyboardButton(text=LEXICON_COMMANDS["profession"]),
            KeyboardButton(text=LEXICON_COMMANDS["salary"])
        ],
        [
            KeyboardButton(text=LEXICON_COMMANDS["employment"]),
            KeyboardButton(text=LEXICON_COMMANDS["duration"])
        ],
        [
            KeyboardButton(text=LEXICON_COMMANDS["export_file"])
        ],
        [
            KeyboardButton(text=LEXICON_COMMANDS["back"])
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

EmploymentMenu = ReplyKeyboardMarkup(
    keyboard=[
        [
            KeyboardButton(text=LEXICON_COMMANDS["full_time"]),
            KeyboardButton(text=LEXICON_COMMANDS["part_time"])
        ],
        [
            KeyboardButton(text=LEXICON_COMMANDS["remote_employment"]),
            KeyboardButton(text=LEXICON_COMMANDS["all_employment"])
        ],
        [
            KeyboardButton(text=LEXICON_COMMANDS["export_file"])
        ],
        [
            KeyboardButton(text=LEXICON_COMMANDS["back"])
        ]
    ],
    resize_keyboard=True,
    input_field_placeholder="Выберите занятость"
)


SalaryMenu = ReplyKeyboardMarkup(
    keyboard=[
        [
            KeyboardButton(text=LEXICON_COMMANDS["no_salary"]),
            KeyboardButton(text=LEXICON_COMMANDS["with_salary"])
        ],
        [
            KeyboardButton(text=LEXICON_COMMANDS["export_file"])
        ],
        [
            KeyboardButton(text=LEXICON_COMMANDS["back"])
        ]
    ],
    resize_keyboard=True,
    input_field_placeholder="Выберите вариант оклада"
)


DurationMenu = ReplyKeyboardMarkup(
    keyboard=[
        [
            KeyboardButton(text=LEXICON_COMMANDS["up_to_1_month"]),
            KeyboardButton(text=LEXICON_COMMANDS["1_to_3_months"])
        ],
        [
            KeyboardButton(text=LEXICON_COMMANDS["3_months_or_more"]),
            KeyboardButton(text=LEXICON_COMMANDS["all_durations"])
        ],
        [
            KeyboardButton(text=LEXICON_COMMANDS["export_file"])
        ],
        [
            KeyboardButton(text=LEXICON_COMMANDS["back"])
        ]
    ],
    resize_keyboard=True,
    input_field_placeholder="Выберите длительность"
)


# Функция для генерации клавиатуры с сайтами
def sites_keyboard() -> ReplyKeyboardMarkup:
    "Функция, генерирующая клавиатуру со списком сайтов."
    keyboard = []
    row_count = len(LEXICON_COMMANDS["sites"]) // 2
    row_count += len(LEXICON_COMMANDS["sites"]) % 2

    step = 0
    for _ in range(row_count):
        if step + 2 <= len(LEXICON_COMMANDS["sites"]):
            row = [KeyboardButton(text=LEXICON_COMMANDS["sites"][j]) for j in range(step, step + 2)]
        else:
            row = [KeyboardButton(text=LEXICON_COMMANDS["sites"][-1])]
        keyboard.append(row)
        step += 2

    keyboard.append([KeyboardButton(text=LEXICON_COMMANDS["all_sites"]), KeyboardButton(text=LEXICON_COMMANDS["next"])])
    keyboard.append([KeyboardButton(text=LEXICON_COMMANDS["back"])])

    return ReplyKeyboardMarkup(
        keyboard=keyboard,                         # Клавиатура с кнопками
        resize_keyboard=True,                      # Автоматическая настройка размера клавиатуры
        one_time_keyboard=False,                   # Клавиатура не скрывается после использования
        input_field_placeholder="Список сайтов"    # Подсказка для поля ввода
    )
