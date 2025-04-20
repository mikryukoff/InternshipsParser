-- Удаляем существующую базу данных, если она есть
DROP DATABASE IF EXISTS internships_parser;

-- Создаем новую базу данных
CREATE DATABASE internships_parser;

-- Выбираем созданную БД для работы
USE internships_parser;

/*
 * Блок подготовки к пересозданию таблиц
 * Отключаем проверку внешних ключей для безопасного удаления зависимых таблиц
 */
SET FOREIGN_KEY_CHECKS = 0;

-- Удаляем таблицы в порядке зависимостей (от самых зависимых к независимым)
DROP TABLE IF EXISTS internship_employment;  -- Связующая таблица
DROP TABLE IF EXISTS internships;            -- Основная таблица стажировок
DROP TABLE IF EXISTS employment_types;       -- Таблица типов занятости
DROP TABLE IF EXISTS sources;                -- Таблица источников вакансий

-- Включаем проверку внешних ключей после завершения операций удаления
SET FOREIGN_KEY_CHECKS = 1;

/*
 * Создание таблицы источников данных
 * Хранит информацию о сайтах-источниках вакансий
 */
CREATE TABLE sources (
    id INT AUTO_INCREMENT PRIMARY KEY,         -- ID
    source_name VARCHAR(100) UNIQUE NOT NULL,  -- Уникальное название источника
    base_url TEXT NOT NULL                     -- Базовый URL сайта-источника
) ENGINE=InnoDB;

/*
 * Таблица типов занятости
 * Справочник возможных форматов занятости (полная, частичная и т.д.)
 */
CREATE TABLE employment_types (
    id INT AUTO_INCREMENT PRIMARY KEY,        -- ID
    name VARCHAR(50) UNIQUE NOT NULL          -- Уникальное название типа занятости
) ENGINE=InnoDB;

/*
 * Основная таблица стажировок
 * Содержит основную информацию о вакансиях
 */
CREATE TABLE internships (
    id INT AUTO_INCREMENT PRIMARY KEY,       -- ID
    title TEXT NOT NULL,                     -- Название вакансии
    profession TEXT,                         -- Профессия/специальность
    company_name TEXT,                       -- Название компании
    salary_from DECIMAL(10,2),               -- Минимальный уровень зарплаты
    salary_to DECIMAL(10,2),                 -- Максимальный уровень зарплаты
    duration TEXT,                           -- Длительность стажировки
    source_name VARCHAR(100) NOT NULL,       -- Название источника (внешний ключ)
    link TEXT NOT NULL,                      -- Ссылка на вакансию
    description TEXT,                        -- Полное описание вакансии
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,          -- Дата создания записи
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,  -- Дата обновления
    FOREIGN KEY (source_name) REFERENCES sources(source_name)  -- Связь с источниками
) ENGINE=InnoDB;

/*
 * Связующая таблица "многие-ко-многим"
 * Связывает стажировки с типами занятости
 */
CREATE TABLE internship_employment (
    internship_id INT NOT NULL,              -- ID стажировки
    employment_id INT NOT NULL,              -- ID типа занятости
    PRIMARY KEY (internship_id, employment_id),  -- Составной первичный ключ
    FOREIGN KEY (internship_id) REFERENCES internships(id) ON DELETE CASCADE,  -- Удаление связей при удалении стажировки
    FOREIGN KEY (employment_id) REFERENCES employment_types(id)                -- Связь с типами занятости
) ENGINE=InnoDB;

/*
 * Начальное заполнение таблицы источников
 * Используем INSERT IGNORE для предотвращения дубликатов
 */
INSERT IGNORE INTO sources (source_name, base_url) VALUES
('hh.ru', 'https://hh.ru'),
('trudvsem.ru', 'https://trudvsem.ru'),
('superjob.ru', 'https://www.superjob.ru'),
('career.habr.com', 'https://career.habr.com/');