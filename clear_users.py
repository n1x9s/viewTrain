import asyncio
from sqlalchemy import text
from app.dao.database import async_session_maker

async def clear_users():
    async with async_session_maker() as session:
        # Сначала удаляем связи
        await session.execute(text("DELETE FROM user_direction;"))
        await session.execute(text("DELETE FROM user_language;"))
        # Затем удаляем пользователей
        await session.execute(text("DELETE FROM users;"))
        await session.commit()
        print("All users have been deleted")

if __name__ == "__main__":
    asyncio.run(clear_users()) 