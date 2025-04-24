import aiomysql
import asyncio
from config.config import load_config, Config


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
        employment: str,
        source_name: str,
        link: str,
        description: str
    ) -> None:
        """
        Добавляет новую запись о стажировке в таблицу internships и связывает её с типами занятости.

        Аргументы:
            title: (str): Названия объявления о стажировке.
            profession: (str): Название профессии.
            company_name: (str): Название компании, ищущей стажера.
            salary_from: (int): Минимальная зарплата.
            salary_to: (int): Максимальная зарплата.
            duration: (str): Длительность стажировки.
            employment: (str): Тип занятости.
            source_name: (str): Название источника.
            link: (str): Ссылка на объявление.
            description: (str): Описание стажировки (Что не попало под шаблон).
        """
        async with self.connection_pool.acquire() as connection:
            async with connection.cursor() as cursor:
                insert_internship = f"""
                    INSERT INTO internships (title, profession, company_name, salary_from, salary_to, duration, source_name, link, description)
                    VALUES ('{title}', '{profession}', '{company_name}', '{salary_from}', '{salary_to}', '{duration}', '{source_name}', '{link}', '{description}');
                """
                await cursor.execute(insert_internship)

                # Получаем ID стажировки
                internship_id = cursor.lastrowid

                # Цикл для добавления типов занятости, которых нет в таблице
                while True:
                    try:
                        # Получаем ID типа занятости
                        await cursor.execute(f"SELECT id FROM employment_types WHERE name = '{employment}'")
                        row = await cursor.fetchone()
                        employment_id = row[0]
                        break
                    except TypeError:
                        await cursor.execute(f"INSERT IGNORE INTO employment_types (name) VALUES ('{employment}');")

                # Связываем их
                add_relation = f"""
                INSERT INTO internship_employment (internship_id, employment_id)
                VALUES ('{internship_id}', '{employment_id}')
                """
                await cursor.execute(add_relation)

    async def select_internship_data(self, **kwargs) -> tuple:
        """
        Получает данные о стажировке с типами занятости по фильтрам.

        Аргументы:
            kwargs: Возможные фильтры:
                profession: (str): Название профессии.
                company_name: (str): Название компании.
                salary_from: (int): Минимальная зарплата.
                salary_to: (int): Максимальная зарплата.
                duration: (str): Длительность стажировки.
                source_name: (str): Название источника.
                employment_type: (str): Тип занятости (фильтр по точному совпадению)

        Возвращает:
            tuple: Кортеж с данными стажировок и их типами занятости
        """
        async with self.connection_pool.acquire() as connection:
            async with connection.cursor() as cursor:
                query = """
                    SELECT
                        i.*,
                        GROUP_CONCAT(et.name SEPARATOR ', ') AS employment_types
                    FROM internships i
                    LEFT JOIN internship_employment ie ON i.id = ie.internship_id
                    LEFT JOIN employment_types et ON ie.employment_id = et.id
                    WHERE 1=1
                """

                employment_type_filter = ""
                if 'employment_type' in kwargs:
                    employment_type_filter = """
                        AND EXISTS (
                            SELECT 1
                            FROM internship_employment ie2
                            JOIN employment_types et2 ON ie2.employment_id = et2.id
                            WHERE ie2.internship_id = i.id
                            AND et2.name = %(employment_type)s
                        )
                    """
                    kwargs.pop('employment_type')

                params = {}
                filters = []

                column_map = {
                    'source_name': 'i.source_name',
                    'profession': 'i.profession',
                    'company_name': 'i.company_name',
                    'salary_from': 'i.salary_from',
                    'salary_to': 'i.salary_to',
                    'duration': 'i.duration_text'
                }

                for key, value in kwargs.items():
                    if value is None:
                        continue
                    # Проверяем, поддерживается ли ключ
                    if key not in column_map:
                        continue

                    # Обработка списков
                    if isinstance(value, (list, tuple)):
                        if not value:  # Пустой список игнорируем
                            continue
                        filters.append(f"{column_map[key]} IN %({key})s")
                        params[key] = tuple(value)
                    else:
                        filters.append(f"{column_map[key]} = %({key})s")
                        params[key] = value

                full_query = query
                if filters:
                    full_query += " AND " + " AND ".join(filters)

                full_query += employment_type_filter
                full_query += " GROUP BY i.id"

                await cursor.execute(full_query, params)
                result = await cursor.fetchall()

        return result

    async def update_internships(self, source_name: str) -> None:
        pass


async def initialize_databases() -> tuple:
    """
    Инициализирует соединения с базами данных для таблиц.

    Создает экземпляры классов, устанавливает
    соединения с базами данных и возвращает их.

    Возвращает:
        tuple: Кортеж, содержащий экземпляры классов.
    """
    sources_table = Sources(
        config.database.host,
        config.database.user,
        config.database.password,
        config.database.db_name,
    )

    internships_table = Internships(
        config.database.host,
        config.database.user,
        config.database.password,
        config.database.db_name,
    )

    await sources_table.connect()
    await internships_table.connect()

    return sources_table, internships_table
