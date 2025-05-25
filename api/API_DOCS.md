### Документация к API

#### Базовый URL
`http://ваш_сервер:8000`

---

## 1. Получение стажировок с фильтрами
`GET /internships/filters`

### Параметры запроса:
| Параметр          | Тип    | Обязательный | Описание                                 | Пример значения       |
|-------------------|--------|--------------|-----------------------------------------|-----------------------|
| `response_format` | string | Нет          | Формат ответа: `json` (по умолчанию) или `file` | `file`                |
| `limit`           | int    | Нет          | Количество записей (1-1000)             | `50`                  |
| `offset`          | int    | Нет          | Смещение (пагинация)                    | `100`                 |
| `profession`      | string | Нет          | Фильтр по профессии (возможно перечисление через ",") | `Программист`         |
| `company_name`    | string | Нет          | Фильтр по компании (возможно перечисление через ",") | `Яндекс`              |
| `salary_from`     | int    | Нет          | Минимальная зарплата                    | `50000`               |
| `salary_to`       | int    | Нет          | Максимальная зарплата                   | `150000`              |
| `source_name`     | string | Нет          | Источник вакансии (hh.ru или trudvsem.ru) | `hh.ru`               |
| `employment_type` | string | Нет          | Тип занятости (возможно перечисление через ",") | `Полная занятость`    |
| `description`     | string | Нет          | Поиск по описанию                      | `удаленная работа`    |

### Пример запроса:
```http
GET /internships/filters?profession=Программист&salary_from=10000&limit=20&response_format=file
```

### Успешный ответ (200):
**JSON-формат:**
```json
{
  "data": [
    {
      "id": 484,
      "title": "Стажер-разработчик бэкенда",
      "profession": "Программист, разработчик",
      "company_name": "Яндекс",
      "salary_from": "20000.00",
      "salary_to": "70000.00",
      "source_name": "hh.ru",
      "link": "https://hh.ru/vacancy/120470870",
      "description": "Оплачиваемая стажировка в сервисах и продуктах Яндекса.",
      "created_at": "2025-05-14 15:31:12",
      "employment_types": "Частичная занятость"
    },
  ],
  "pagination": {
    "total": 150,
    "limit": 20,
    "offset": 0,
    "has_more": true
  }
}
```

**Файловый формат:**  
Возвращает файл `internships.json` с аналогичной структурой.

---

## 2. Поиск по ключевым словам
`GET /internships/keywords`

### Параметры запроса:
| Параметр          | Тип    | Обязательный | Описание                                 | Пример значения       |
|-------------------|--------|--------------|-----------------------------------------|-----------------------|
| `keywords`        | string | Да           | Ключевые слова через запятую. Исключения с `-` | `python, -java`       |
| `salary_from`     | int    | Нет          | Минимальная зарплата                    | `60000`               |
| `salary_to`       | int    | Нет          | Максимальная зарплата                   | `200000`              |
| `employment_type` | string | Нет          | Тип занятости (возможно перечисление через ",") | `Удаленная работа`    |

### Пример запроса:
```http
GET /internships/keywords?keywords=python,-java&salary_from=80000&employment_type=Удаленная
```

### Ответ:  
Аналогичен формату из раздела 1.

---

## 3. Обновление базы данных
`PUT /internships/update_db`

### Описание:  
Запускает парсинг вакансий с TrudVsem и HeadHunter.

### Пример запроса:
```http
PUT /internships/update_db
```

### Успешный ответ (200):
```json
{
  "status": "success",
  "updated": true
}
```

### Ошибки:
- `500 Internal Server Error` при проблемах с парсингом

---

## Общие элементы

### Формат ошибок:
```json
{
  "detail": "Текст ошибки"
}
```

### Коды статусов:
- `200 OK`: Успешный запрос
- `400 Bad Request`: Невалидные параметры
- `500 Internal Server Error`: Ошибка сервера

---

## Пример использования cURL

1. Получение данных в JSON:
```bash
curl -X GET "http://localhost:8000/internships/filters?profession=Аналитик&limit=5"
```

2. Скачивание файла:
```bash
curl -X GET "http://localhost:8000/internships/filters?response_format=file" --output internships.json
```
