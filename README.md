# Парсер стажировок с сайтов hh.ru и trudvsem.ru

## API Documentation

### Базовый URL
`http://ваш_сервер:8000`

### Доступ:
1. `http://ваш-сервер:8000/docs` (интерактивная документация)
2. `http://ваш-сервер:8000/redoc` (альтернативный вариант)
3. [Файл документации](api/API_DOCS.md)

## Установка

**1. Установите Docker на вашу ОС:**

- Для Windows: установите Docker-desktop с [официального сайта](https://www.docker.com/products/docker-desktop/).

- Для Linux дистрибутивов следуйте [инструкции](https://docs.docker.com/engine/install/).

**2. Склонируйте репозиторий:**
```bash
git clone https://github.com/mikryukoff/InternshipsParser.git
```

**3. Создайте файл .env, c необходимыми переменными окружения (пример ниже):**
```makefile
BOT_TOKEN="4342342335:AAfwmfdlkIJLKSFjlkd_234adwalkWLKJ"    # Токен телеграм-бота (вставьте свой)

DB_HOST="db"                                                # Хост БД (оставьте так) 
DB_USER="root"                                              # Имя администратора БД (вставьте своё)
DB_PASSWORD=""                                              # Пароль от БД (вставьте свой)
DB_NAME="db_bot"                                            # Название БД (вставьте своё)
```

## Запуск

**1. Сборка и запуск Docker'а:**
```bash
docker-compose up --build -d
```

**2. Остановка Docker'а:**
```bash
docker-compose down
```

## Схема каталогов проекта

```plaintext
InternshipsParser/
├── api/                    # Сервис API (FastAPI/Uvicorn)
│   ├── __init__.py
│   ├── main.py             # Точка входа API
│   └── models.py           # Модели Pydantic
│
├── bot/                    # Telegram-bot
│   ├── __init__.py
│   ├── __main__.py         # Точка входа бота
│   ├── admin_handlers.py   # Обработчики админ-команд
│   ├── filters_handlers.py # Обработчик фильтров парсинга
│   ├── menu_handlers.py    # Обработчики меню
│   ├── filters.py          # Пользовательские фильтры
│   ├── lexicon.py          # Тексты и локализация
│   └── menu_kb.py          # Генератор клавиатур
│
├── common/                 # Общие модули
│   ├── __init__.py
│   ├── config.py           # Конфигурация приложения
│   ├── database.py         # Код взаимодействия с MySQL
│   ├── hh_parser.py        # Парсер hh.ru
│   ├── trudvsem_parser.py  # Парсер trudvsem.ru
│   └── logger.py           # Настройка логгера
│
├── mysql_migrations/       # SQL-миграции БД
│   └── database.sql        # Скрипт создания БД
│
├── .dockerignore           # Исключения для Docker
├── .env.example            # Шаблон .env
├── .gitignore              # Исключения Git
├── docker-compose.yml      # Конфигурация сервисов
├── Dockerfile.api          # Сборка образа API
├── Dockerfile.bot          # Сборка образа бота
├── logs.log                # Общий лог-файл
├── README.md               # Документация
└── requirements.txt        # Зависимости Python
```