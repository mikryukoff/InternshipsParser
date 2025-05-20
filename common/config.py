from dataclasses import dataclass

from environs import Env


# Описание настроек подключения к БД
@dataclass
class Database:
    host: str        # Хост БД
    user: str        # Имя пользователя БД
    password: str    # Пароль от БД
    db_name: str     # Название БД


# Конфиг для настройки Telegram-бота
@dataclass
class TgBot:
    token: str


# Основной конфиг приложения
@dataclass
class Config:
    tg_bot: TgBot           # Конфигурация Telegram-бота
    database: Database      # Данные для подключения к БД


# Функция загрузки конфигурации
def load_config(path: str | None = None) -> Config:
    # Инициализация окружения
    env = Env()
    env.read_env(path)

    # Возврат конфигурации
    return Config(
        tg_bot=TgBot(token=env("BOT_TOKEN")),    # Токен Telegram-бота
        database=Database(
            host=env("DB_HOST"),                 # Хост БД
            user=env("DB_USER"),                 #
            password=env("DB_PASSWORD"),         # Пароль от БД
            db_name=env("DB_NAME")               # Название БД
        )
    )
