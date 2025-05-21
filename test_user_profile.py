from app.auth.dao import UsersDAO
from app.dao.session_maker import async_session_maker
import asyncio

async def test_user_profile():
    """Тестирует загрузку связей пользователя и определение типа вопросов"""
    from app.interview.dao import QuestionDAO
    
    async with async_session_maker() as session:
        # Получаем пользователя с ID 1 со всеми связями
        user = await UsersDAO.find_user_with_relations(session, 1)
        
        if not user:
            print("Пользователь с ID 1 не найден")
            return
            
        # Выводим информацию о языках пользователя
        print("User languages:", [lang.name for lang in user.languages] if user.languages else [])
        
        # Выводим информацию о направлениях пользователя
        print("User directions:", [dir.name for dir in user.directions] if user.directions else [])
        
        # Определяем тип вопросов для пользователя
        question_type = QuestionDAO.get_question_type_for_user(user)
        print(f"Question type for user: {question_type}")

if __name__ == "__main__":
    asyncio.run(test_user_profile()) 