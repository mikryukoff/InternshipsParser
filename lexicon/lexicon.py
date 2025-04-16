# Словарь для выполнения запросов ботом по запросам,
# где ключ - запрос от пользователя,
# значение - команда боту
LEXICON_COMMANDS: dict[str, str] = {
    "filters": "Фильтры",
    "admin_panel": "Admin-панель",
    "update_db": "Обновить БД",
    "export_file": "Выгрузка файла",
    
    "add_admin": "Добавить администратора",
    
    "sites": ["hh.ru", "trudvsem.ru", "Rabota.ru", "SuperJob.ru"],
    "all_sites": "Все сайты",
    "next": "Далее",
    "back": "Назад",
    
    "profession": "Профессия",
    "salary": "Оклад",
    "employment": "Занятость",
    "duration": "Длительность",

    "full_time": "Полная",
    "part_time": "Неполная",
    "remote_employment": "Удаленная",
    "all_employment": "Выбрать все",
    
    "no_salary": "Без оклада",
    "with_salary": "Есть оклад",
    
    "up_to_1_month": "До 1 месяца",
    "1_to_3_months": "От 1 до 3 месяцев",
    "3_months_or_more": "От 3 месяцев",
    "all_durations": "Выбрать все"

}

# Словарь для текстовых ответов бота по запросам,
# где ключ - запрос от пользователя,
# значение - ответ бота
LEXICON: dict[str, str] = {
    "/start": "✋ Привет,\n🤖 Меня зовут InternshipBot.",
    "admin_welcome": "🔐 Добро пожаловать в админ-панель!",
    "unvailable": "😊 Извините, данная функция в разработке.",
    "select_site": "Выберите сайт для поиска:",
    "select_filters": "Выберите фильтры:",
    "select_employment": "Выберите занятость стажировки:",
    "select_salary": "Выберите сумму оклада:",
    "select_duration": "Выберите период стажировки:",
    "selected_option": "Выбрано: {}",
    "selected_site": "Выбранный сайт: {}"
}