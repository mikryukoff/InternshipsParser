# Словарь для текстовых ответов бота по запросам,
# где ключ - запрос от пользователя,
# значение - ответ бота
LEXICON: dict[str, str] = {
    "/start": "✋ Привет,\n🤖 Меня зовут InternshipBot.",
    "unvailable": "😊 Извините, данная функция в разработке.",
    "to_main_menu": "👣 Вы вернулись в главное меню!",
    "processing": "🧠 Обрабатываю запрос... Пожалуйста, подождите...",
    }

# Словарь для выполнения запросов ботом по запросам,
# где ключ - запрос от пользователя,
# значение - команда боту
LEXICON_COMMANDS: dict[str, str] = {
    "to_main_menu": "️🔙 В главное меню",
    "admin_panel": "Админ-панель",
    "to_filters": "Фильтры"
}
