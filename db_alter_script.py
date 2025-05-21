import asyncio
import os
import asyncpg
from dotenv import load_dotenv

# Загружаем переменные окружения из файла .env
load_dotenv()

# Получаем данные для подключения из переменных окружения
DB_HOST = os.getenv("DB_HOST", "localhost")
DB_PORT = os.getenv("DB_PORT", "5432")
DB_NAME = os.getenv("DB_NAME", "interview")
DB_USER = os.getenv("DB_USER", "postgres")
DB_PASS = os.getenv("DB_PASS", "postgres")

async def add_columns():
    """Добавляет колонки question_type в таблицы interviews и user_answers"""
    # Создаем строку подключения
    dsn = f"postgresql://{DB_USER}:{DB_PASS}@{DB_HOST}:{DB_PORT}/{DB_NAME}"
    
    # Подключаемся к базе данных
    conn = await asyncpg.connect(dsn)
    try:
        # Проверяем наличие колонки question_type в таблице interviews и добавляем ее, если она не существует
        interview_column_exists = await conn.fetchval(
            "SELECT EXISTS (SELECT 1 FROM information_schema.columns WHERE table_name='interviews' AND column_name='question_type')"
        )
        
        if not interview_column_exists:
            print("Добавляем колонку question_type в таблицу interviews")
            await conn.execute(
                "ALTER TABLE interviews ADD COLUMN question_type VARCHAR DEFAULT 'pythonn' NOT NULL"
            )
            print("Колонка question_type успешно добавлена в таблицу interviews")
        else:
            print("Колонка question_type уже существует в таблице interviews")
        
        # Проверяем наличие колонки question_type в таблице user_answers и добавляем ее, если она не существует
        answer_column_exists = await conn.fetchval(
            "SELECT EXISTS (SELECT 1 FROM information_schema.columns WHERE table_name='user_answers' AND column_name='question_type')"
        )
        
        if not answer_column_exists:
            print("Добавляем колонку question_type в таблицу user_answers")
            await conn.execute(
                "ALTER TABLE user_answers ADD COLUMN question_type VARCHAR DEFAULT 'pythonn' NOT NULL"
            )
            print("Колонка question_type успешно добавлена в таблицу user_answers")
        else:
            print("Колонка question_type уже существует в таблице user_answers")
    
    finally:
        # Закрываем соединение с базой данных
        await conn.close()

if __name__ == "__main__":
    # Запускаем асинхронную функцию
    asyncio.run(add_columns()) 