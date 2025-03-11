# Interview Training API

Система для проведения тренировочных интервью с автоматической оценкой ответов.

## Технологический стек

- Python 3.11+
- FastAPI
- SQLAlchemy 2.0
- PostgreSQL
- Alembic (миграции)
- Pydantic v2

## Локальное развертывание

### 1. Клонирование репозитория

```bash
git clone <your-repository-url>
cd interviewTraining
```

### 2. Создание виртуального окружения

```bash
python -m venv .venv
source .venv/bin/activate  # для Linux/macOS
# или
.venv\Scripts\activate  # для Windows
```

### 3. Установка зависимостей

```bash
pip install -r requirements.txt
```

### 4. Настройка базы данных

1. Установите PostgreSQL, если он еще не установлен
2. Создайте базу данных:

```bash
createdb interview_training
```

3. Синхронизируйте данные .env с репозитория со своими данными подключения к базе данных


### 5. Применение миграций

```bash
alembic upgrade head
```

### 6. Запуск сервера для разработки

```bash
uvicorn app.main:app --reload
```

Сервер будет доступен по адресу: http://localhost:8000

API документация: http://localhost:8000/docs

## Структура проекта

```
app/
├── auth/               # Аутентификация и авторизация
│   ├── dependencies.py # Зависимости для авторизации
│   ├── models.py      # Модели пользователей
│   ├── router.py      # Роуты аутентификации
│   └── schemas.py     # Схемы данных
├── dao/               # Доступ к данным
│   ├── base.py       # Базовый класс DAO
│   ├── database.py   # Настройки базы данных
│   └── session.py    # Управление сессиями
├── history/          # История интервью
│   ├── dao.py       # Доступ к данным истории
│   ├── router.py    # Роуты истории
│   └── schemas.py   # Схемы истории
├── interview/        # Основной функционал интервью
│   ├── dao.py       # Доступ к данным интервью
│   ├── models.py    # Модели интервью и вопросов
│   ├── router.py    # Роуты интервью
│   └── schemas.py   # Схемы интервью
└── main.py          # Точка входа приложения
```
