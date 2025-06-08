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
            employment: (str): Тип занятости.
            source_name: (str): Название источника.
            link: (str): Ссылка на объявление.
            description: (str): Описание стажировки (Что не попало под шаблон).
        """
        async with self.connection_pool.acquire() as connection:
            async with connection.cursor() as cursor:
                insert_internship = f"""
                    INSERT INTO internships (title, profession, company_name, salary_from, salary_to, source_name, link, description)
                    VALUES ('{title}', '{profession}', '{company_name}', '{salary_from}', '{salary_to}', '{source_name}', '{link}', '{description}');
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
                source_name: (str): Название источника.
                employment_type: (str): Тип занятости
                description: (str): Описание стажировки (что не попало под шаблон)

        Возвращает:
            tuple: Кортеж с данными стажировок и их типами занятости
        """

        base_query = """
            SELECT
                i.*,
                GROUP_CONCAT(DISTINCT et.name ORDER BY et.name SEPARATOR ', ') AS employment_types
            FROM internships i
            LEFT JOIN internship_employment ie ON i.id = ie.internship_id
            LEFT JOIN employment_types et ON ie.employment_id = et.id
            WHERE 1=1
        """
        params = {}
        conditions = []

        employment_cond = self._build_employment_condition(
            kwargs.pop('employment_type', []),
            params
        )
        if employment_cond:
            conditions.append(employment_cond)

        conditions += self._build_salary_conditions(kwargs, params)

        conditions += self._build_text_conditions(params, kwargs)

        return await self._execute_query(
            base_query, params, conditions, limit=10000
        )

    async def select_internship_data_by_keywords(self, **kwargs) -> tuple:
        """
        Получает данные о стажировке с типами занятости по ключевым словам c поддержкой исключений.

        Аргументы:
            kwargs: Возможные фильтры:
                keywords: (list): Ключевые слова для поиска. Слова, начинающиеся с '-', исключают записи.
                salary_from: (int): Минимальная зарплата.
                salary_to: (int): Максимальная зарплата.
                employment_type: (str): Тип занятости

        Возвращает:
            tuple: Кортеж с данными стажировок и их типами занятости.
        """

        base_query = """
            SELECT
                i.*,
                GROUP_CONCAT(DISTINCT et.name ORDER BY et.name SEPARATOR ', ') AS employment_types
            FROM internships i
            LEFT JOIN internship_employment ie ON i.id = ie.internship_id
            LEFT JOIN employment_types et ON ie.employment_id = et.id
            WHERE 1=1
        """
        params = {}
        conditions = []

        include, exclude = self._parse_keywords(kwargs.pop('keywords', ''))
        text_columns = [
            'i.profession', 'i.title', 'i.company_name',
            'i.source_name', 'i.description'
        ]

        logger.debug("Include conditions: %s", include)
        logger.debug("Exclude conditions: %s", exclude)

        include_conds = self._build_include_conditions(include, text_columns, params)
        if include_conds:
            conditions.append(include_conds)

        exclude_conds = self._build_exclude_conditions(exclude, text_columns, params)
        if exclude_conds:
            conditions.append(exclude_conds)

        employment_cond = self._build_employment_condition(
            kwargs.pop('employment_type', []),
            params
        )
        if employment_cond:
            conditions.append(employment_cond)

        conditions += self._build_salary_conditions(kwargs, params)

        return await self._execute_query(base_query, params, conditions)

    def _parse_keywords(self, keywords: str) -> tuple:
        """Парсит ключевые слова на включающие и исключающие."""
        include = []
        exclude = []

        for word in keywords:
            word = word.strip().lower()
            if not word:
                continue
            if word.startswith('-'):
                exclude.append(word[1:])
            else:
                include.append(word)

        return include, exclude

    async def _execute_query(
        self,
        base_query: str,
        params: dict,
        conditions: list,
        limit: int = 100,
        offset: int = 0
    ) -> tuple:
        """Выполняет SQL-запрос с параметрами."""
        full_query = base_query
        if conditions:
            full_query += " AND " + " AND ".join(conditions)
        full_query += " GROUP BY i.id LIMIT %(limit)s OFFSET %(offset)s"

        params.update({
            'limit': limit,
            'offset': offset
        })

        async with self.connection_pool.acquire() as connection:
            async with connection.cursor() as cursor:
                await cursor.execute(full_query, params)
                return await cursor.fetchall()

    def _build_like_conditions(
        self,
        values: str | list[str],
        columns: list[str],
        params: dict,
        param_prefix: str
    ) -> str:
        """Общая функция для построения условий LIKE."""
        if not values:
            return ""

        if isinstance(values, str):
            values = [values]

        conditions = []
        for idx, value in enumerate(values):
            value = value.strip().lower()
            column_conditions = []
            for col_idx, column in enumerate(columns):
                param_name = f"{param_prefix}_{idx}_{col_idx}"
                column_conditions.append(f"{column} LIKE %({param_name})s")
                params[param_name] = f"%{value}%"
            conditions.append(f"({' OR '.join(column_conditions)})")

        return " OR ".join(conditions)

    def _build_employment_condition(self, employment_types: list, params: dict) -> str:
        """Условие для занятости с использованием общей функции."""
        if not employment_types:
            return ""

        conditions_str = self._build_like_conditions(
            values=employment_types,
            columns=["et2.name"],
            params=params,
            param_prefix="employment_type"
        )

        return f"""
            EXISTS (
                SELECT 1
                FROM internship_employment ie2
                JOIN employment_types et2 ON ie2.employment_id = et2.id
                WHERE ie2.internship_id = i.id
                AND ({conditions_str})
            )
        """

    def _build_text_conditions(self, params: dict, filters: dict) -> list:
        """Унифицированная обработка текстовых фильтров."""
        text_columns = {
            'profession': ['i.profession', 'i.title'],
            'company_name': ['i.company_name'],
            'source_name': ['i.source_name'],
            'description': ['i.description']
        }

        conditions = []
        for key, columns in text_columns.items():
            value = filters.get(key)
            if not value:
                continue

            conditions_str = self._build_like_conditions(
                values=value,
                columns=columns,
                params=params,
                param_prefix=f"{key}_like"
            )

            if conditions_str:
                conditions.append(f"({conditions_str})")

        return conditions

    def _build_salary_conditions(self, kwargs: dict, params: dict) -> list:
        """Добавляет условия по зарплате."""
        conditions = []
        if 'salary_from' in kwargs and kwargs['salary_from'] is not None:
            conditions.append("i.salary_from >= %(salary_from)s")
            params['salary_from'] = kwargs.pop('salary_from')

        if 'salary_to' in kwargs and kwargs['salary_to'] is not None:
            conditions.append("i.salary_to <= %(salary_to)s")
            params['salary_to'] = kwargs.pop('salary_to')

        return conditions

    def _build_include_conditions(self, words: list, columns: list, params: dict) -> str:
        """Строит условия для включения ключевых слов (логическое ИЛИ между словами)."""
        if not words:
            return ""

        conditions = []
        for idx, word in enumerate(words):
            word_conds = []
            for col_idx, column in enumerate(columns):
                param_name = f"inc_{idx}_{col_idx}"
                word_conds.append(f"{column} LIKE %({param_name})s")
                params[param_name] = f"%{word}%"
            conditions.append(f"({' OR '.join(word_conds)})")

        # Объединяем условия через OR
        return f"({' OR '.join(conditions)})" if conditions else ""

    def _build_exclude_conditions(self, words: list, columns: list, params: dict) -> str:
        """Строит условия для исключения ключевых слов (логическое И между словами)."""
        if not words:
            return ""

        conditions = []
        for idx, word in enumerate(words):
            word_conds = []
            for col_idx, column in enumerate(columns):
                param_name = f"exc_{idx}_{col_idx}"
                word_conds.append(f"{column} NOT LIKE %({param_name})s")
                params[param_name] = f"%{word}%"
            conditions.append(f"({' AND '.join(word_conds)})")

        # Объединяем условия через AND
        return f"({' AND '.join(conditions)})" if conditions else ""

    async def update_internships(self, days: int = 7) -> None:
        """
        Удаляет старые записи стажировок из базы данных.
        Аргументы:
            days: (int): Промежуток для определения устаревших записей.
        """
        async with self.connection_pool.acquire() as connection:
            async with connection.cursor() as cursor:
                # Удаляем записи старше указанного количества дней
                delete_query = """
                    DELETE FROM internships
                    WHERE created_at < DATE_SUB(NOW(), INTERVAL %s DAY)
                """
                await cursor.execute(delete_query, (days,))
                affected_rows = cursor.rowcount
        logger.info(f"Удалено устаревших записей: {affected_rows}")


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
