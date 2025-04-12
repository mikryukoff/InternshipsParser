CREATE DATABASE internships_parser;
USE internships_parser;

/*
 * Таблица источников данных (сайтов с вакансиями)
 * Хранит информацию о площадках, с которых парсятся стажировки
 */
CREATE TABLE sources (
    id INT AUTO_INCREMENT PRIMARY KEY,         -- Уникальный идентификатор источника
    name VARCHAR(100) UNIQUE NOT NULL,         -- Название источника
    base_url TEXT NOT NULL                     -- Базовый URL сайта
) ENGINE=InnoDB;                               -- Используем движок InnoDB для поддержки транзакций

/*
 * Таблица типов занятости
 * Содержит возможные варианты занятости (полная, частичная и т.д.)
 */
CREATE TABLE employment_types (
    id INT AUTO_INCREMENT PRIMARY KEY,         -- Уникальный идентификатор типа
    name VARCHAR(50) UNIQUE NOT NULL           -- Название типа занятости
) ENGINE=InnoDB;

/*
 * Основная таблица стажировок
 * Содержит основную информацию о вакансиях
 */
CREATE TABLE internships (
    id INT AUTO_INCREMENT PRIMARY KEY,         -- Уникальный идентификатор стажировки
    title TEXT NOT NULL,                       -- Название вакансии
    profession TEXT,                           -- Профессия/специальность
    company_name TEXT,                         -- Название компании
    salary_from DECIMAL(10,2),                 -- Минимальная зарплата (10 цифр, 2 после запятой)
    salary_to DECIMAL(10,2),                   -- Максимальная зарплата
    duration_text TEXT,                        -- Длительность стажировки в текстовом формате
    source_id INT NOT NULL,                    -- ID источника (внешний ключ)
    link TEXT NOT NULL,                        -- Ссылка на вакансию
    description TEXT,                          -- Описание вакансии
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,                              -- Дата создания записи
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,  -- Дата обновления
    UNIQUE KEY (link(255)),                                                      -- Уникальность ссылки (индекс на первых 255 символах)
    FOREIGN KEY (source_id) REFERENCES sources(id)                               -- Связь с таблицей источников
) ENGINE=InnoDB;

/*
 * Связующая таблица для связи многие-ко-многим
 * между стажировками и типами занятости
 */
CREATE TABLE internship_employment (
    internship_id INT NOT NULL,                -- ID стажировки
    employment_id INT NOT NULL,                -- ID типа занятости
    PRIMARY KEY (internship_id, employment_id),                                -- Составной первичный ключ
    FOREIGN KEY (internship_id) REFERENCES internships(id) ON DELETE CASCADE,  -- Каскадное удаление
    FOREIGN KEY (employment_id) REFERENCES employment_types(id)                -- Связь с типами занятости
) ENGINE=InnoDB;