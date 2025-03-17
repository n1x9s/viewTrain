# Используем Python 3.11
FROM python:3.11-slim

# Устанавливаем рабочую директорию
WORKDIR /app

# Устанавливаем зависимости для сборки и PostgreSQL клиент
RUN apt-get update && apt-get install -y \
    gcc \
    libpq-dev \
    postgresql-client \
    && rm -rf /var/lib/apt/lists/*

# Копируем файлы зависимостей
COPY requirements.txt .

# Устанавливаем зависимости
RUN pip install --no-cache-dir -r requirements.txt

# Копируем код приложения
COPY . .

# Делаем скрипт ожидания исполняемым
RUN chmod +x scripts/wait-for-db.sh

# Создаем директорию для логов
RUN mkdir -p logs && chmod 777 logs

# Создаем пользователя без прав root
RUN adduser --disabled-password --gecos '' appuser

# Устанавливаем переменные окружения для PostgreSQL
ENV PGHOST=db \
    PGPORT=5432

USER appuser

# Команда для запуска приложения
CMD ["./scripts/wait-for-db.sh", "db", "uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"] 