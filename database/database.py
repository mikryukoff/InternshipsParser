import aiomysql
import asyncio
from config.config import load_config, Config
from typing import Union


# Определяем конфиг
config: Config = load_config()


class ConnectTable:
    def __init__(self, host: str, user: str, password: str, db_name: str):
        """
        Инициализирует класс ConnectTable и устанавливает параметры подключения к базе данных.

        Аргументы:
            host (str): Хост базы данных.
            user (str): Имя пользователя для подключения.
            password (str): Пароль для подключения.
            db_name (str): Имя базы данных.
        """
        self.host = host
        self.user = user
        self.password = password
        self.db_name = db_name

    async def connect(self) -> None:
        """
        Создает пул соединений с базой данных.
        """
        self.connection_pool = await aiomysql.create_pool(
            host=self.host,
            user=self.user,
            password=self.password,
            db=self.db_name,
            autocommit=True,
        )

    async def close(self) -> None:
        """
        Закрывает пул соединений с базой данных.
        """
        if self.connection_pool:
            self.connection_pool.close()
            await self.connection_pool.wait_closed()


class Sources(ConnectTable):
    async def is_source_in_the_table(self, source_name: str) -> bool:
        """
        Проверяет, существует ли источник в базе данных.

        Аргументы:
            source_name (str): Название источника.

        Возвращает:
            bool: True, если источник существует, иначе False.
        """
        async with self.connection_pool.acquire() as connection:
            async with connection.cursor() as cursor:
                select_source = f"SELECT * FROM sources WHERE name = {source_name};"
                await cursor.execute(select_source)
                rows = await cursor.fetchone()
            return True if rows else False

    async def insert_source_in_the_table(self, source_name: str, source_url: str) -> None:
        """
        Добавляет источник в таблицу sources.

        Аргументы:
            source_name (str): Название источника.
            source_url (str): Ссылка на источник.
        """
        async with self.connection_pool.acquire() as connection:
            async with connection.cursor() as cursor:
                insert_source_data = f"""
                    INSERT INTO sources (name, base_url)
                    VALUES ({source_name}, '{source_url}';
                """
                await cursor.execute(insert_source_data)

    async def select_source_data(self, source_name: str) -> tuple[str, str]:
        """
        Получает данные источника по его source_name.

        Аргументы:
            source_name (str): Название источника.

        Возвращает:
            tuple[str, str]: Название источника и ссылка на источник.

        Исключение:
            ValueError: Если источник с указанным source_name не найден.
        """
        async with self.connection_pool.acquire() as connection:
            async with connection.cursor() as cursor:
                select = f"""
                    SELECT name, base_url
                    FROM users
                    WHERE name = {source_name};
                """
                await cursor.execute(select)
                row = await cursor.fetchone()

        if not row:
            raise ValueError(f"Источник {source_name} не найден.")

        source_name, source_url = row

        return source_name, source_url


class Internships(ConnectTable):
    async def insert_internship(
        self,
        title: str,
        profession: str,
        company_name: str,
        salary_from: int,
        salary_to: int,
        duration: str,
        source_name: str,
        link: str,
        description: str
    ) -> None:
        """
        Добавляет новую запись о стажировке в таблицу internships.

        Аргументы:
            title: (str): Названия объявления о стажировке.
            profession: (str): Название профессии.
            company_name: (str): Название компании, ищущей стажера.
            salary_from: (int): Минимальная зарплата.
            salary_to: (int): Максимальная зарплата.
            duration: (str): Длительность стажировки.
            source_name: (str): Название источника (id?).
            link: (str): Ссылка на объявление.
            description: (str): Описание стажировки (Что не попало под шаблон).
        """
        async with self.connection_pool.acquire() as connection:
            async with connection.cursor() as cursor:
                insert_internship = f"""
                    INSERT INTO internships (title, profession, company_name, salary_from, salary_to, duration_text, source_id, link, description)
                    VALUES ({title}, '{profession}', '{company_name}', '{salary_from}', '{salary_to}', '{duration}', '{source_name}', '{link}', '{description}');
                """
                await cursor.execute(insert_internship)

    async def select_internship_data(self):
        pass

    async def update_internships(self, source_name: str) -> None:
        pass