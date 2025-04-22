FROM python:3.12.10-slim

# Рабочая директория внутри контейнера
WORKDIR /app

# Копирование файла requirements.txt
COPY requirements.txt /app/

# Установка зависимостей
RUN pip install --no-cache-dir -r requirements.txt

# Копирование остальных файлов проекта
COPY . /app/

# Запуск приложения через __main__.py
CMD ["python", "/app/__main__.py"]