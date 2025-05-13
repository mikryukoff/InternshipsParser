import aiomysql
import asyncio
from common.config import load_config, Config
from common.logger import get_logger


# Определяем конфиг
config: Config = load_config()

logger = get_logger(__name__)


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
                employment_type: (str): Тип занятости
                description: (str): Описание стажировки (что не попало под шаблон)

        Возвращает:
            tuple: Кортеж с данными стажировок и их типами занятости
        """
        logger.info(kwargs)
        async with self.connection_pool.acquire() as connection:
            async with connection.cursor() as cursor:
                base_query = """
                    SELECT
                        i.*,
                        GROUP_CONCAT(et.name SEPARATOR ', ') AS employment_types
                    FROM internships i
                    LEFT JOIN internship_employment ie ON i.id = ie.internship_id
                    LEFT JOIN employment_types et ON ie.employment_id = et.id
                    WHERE 1=1
                """

                params = {}
                conditions = []
                employment_types = kwargs.pop('employment_type', [])

                # Обработка нескольких типов занятости
                if employment_types:
                    if isinstance(employment_types, str):
                        employment_types = [employment_types]

                    placeholders = ", ".join([f"%(_employment_type_{i})s" for i in range(len(employment_types))])
                    conditions.append(f"""
                        EXISTS (
                            SELECT 1
                            FROM internship_employment ie2
                            JOIN employment_types et2 ON ie2.employment_id = et2.id
                            WHERE ie2.internship_id = i.id
                            AND et2.name IN ({placeholders})
                        )
                    """)
                    for i, emp_type in enumerate(employment_types):
                        params[f"_employment_type_{i}"] = emp_type

                # Обработка зарплат
                if 'salary_from' in kwargs and kwargs['salary_from'] is not None:
                    conditions.append("i.salary_from >= %(salary_from)s")
                    params['salary_from'] = kwargs.pop('salary_from')

                if 'salary_to' in kwargs and kwargs['salary_to'] is not None:
                    conditions.append("i.salary_to <= %(salary_to)s")
                    params['salary_to'] = kwargs.pop('salary_to')

                # Обработка текстовых фильтров с частичным совпадением
                text_filters = {
                    'profession': 'i.profession',
                    'company_name': 'i.company_name',
                    'duration': 'i.duration_text',
                    'source_name': 'i.source_name',
                    'description': 'i.description'
                }

                for key, column in text_filters.items():
                    value = kwargs.get(key)
                    if value:
                        # Нормализация: удаление пробелов и приведение к нижнему регистру
                        if isinstance(value, (list, tuple)):
                            value = [v.strip().lower() for v in value]
                        else:
                            value = value.strip().lower()

                        if isinstance(value, (list, tuple)):
                            or_conditions = []
                            for i, item in enumerate(value):
                                param_name = f"{key}_like_{i}"
                                or_conditions.append(f"{column} LIKE %({param_name})s")
                                params[param_name] = f"%{item}%"
                            conditions.append(f"({' OR '.join(or_conditions)})")
                        else:
                            conditions.append(f"{column} LIKE %({key}_like)s")
                            params[f"{key}_like"] = f"%{value}%"

                full_query = base_query
                if conditions:
                    full_query += " AND " + " AND ".join(conditions)
                full_query += " GROUP BY i.id"

                await cursor.execute(full_query, params)
                result = await cursor.fetchall()

        return result

    async def update_internships(self, source_name: str) -> None:
        pass


class EmploymentTypes(ConnectTable):
    async def select_employment_types(self) -> tuple[str]:
        """
        Возвращает все типы занятости.

        Возвращает:
            tuple[str]: Кортеж со всеми доступными типами занятости.
        """
        async with self.connection_pool.acquire() as connection:
            async with connection.cursor() as cursor:
                select = """ SELECT name FROM employment_types; """
                await cursor.execute(select)
                rows = await cursor.fetchall()

        return [row[0] for row in rows]


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
        config.database.db_name
    )

    internships_table = Internships(
        config.database.host,
        config.database.user,
        config.database.password,
        config.database.db_name
    )

    employment_types_table = EmploymentTypes(
        config.database.host,
        config.database.user,
        config.database.password,
        config.database.db_name
    )

    await sources_table.connect()
    await internships_table.connect()
    await employment_types_table.connect()

    return sources_table, internships_table, employment_types_table
