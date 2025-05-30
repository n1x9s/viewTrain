import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession
from app.auth.models import User
from app.interview.models import Interview, Question, UserAnswer
from app.interview.dao import QuestionDAO, InterviewDAO


@pytest.mark.asyncio
async def test_start_interview(
    test_client: AsyncClient, 
    async_session: AsyncSession, 
    test_user: User, 
    auth_headers: dict
):
    """Тест начала интервью"""
    # Создаем тестовые вопросы
    for i in range(15):  # Создаем достаточное количество вопросов для интервью
        question = Question(
            text=f"Test question {i}",
            type=QuestionDAO.get_question_type_for_user(test_user),
            level=1
        )
        await async_session.add(question)
    await async_session.commit()
    
    # Отправляем запрос на начало интервью
    response = await test_client.get("/interview/start", headers=auth_headers)
    
    # Проверяем ответ
    assert response.status_code == 200
    data = response.json()
    assert "id" in data
    assert "user_interview_id" in data
    assert data["total_questions"] > 0


@pytest.mark.asyncio
async def test_get_question(
    test_client: AsyncClient, 
    async_session: AsyncSession, 
    test_user: User, 
    auth_headers: dict
):
    """Тест получения вопроса"""
    # Создаем тестовые вопросы
    for i in range(15):
        question = Question(
            text=f"Test question {i}",
            type=QuestionDAO.get_question_type_for_user(test_user),
            level=1
        )
        await async_session.add(question)
    await async_session.commit()
    
    # Начинаем интервью
    start_response = await test_client.get("/interview/start", headers=auth_headers)
    interview_id = start_response.json()["id"]
    
    # Получаем вопрос
    response = await test_client.get(f"/interview/{interview_id}/question", headers=auth_headers)
    
    # Проверяем ответ
    assert response.status_code == 200
    data = response.json()
    assert "id" in data
    assert "text" in data
    assert "number" in data


@pytest.mark.asyncio
async def test_answer_question(
    test_client: AsyncClient, 
    async_session: AsyncSession, 
    test_user: User, 
    auth_headers: dict
):
    """Тест ответа на вопрос"""
    # Создаем тестовые вопросы
    for i in range(15):
        question = Question(
            text=f"Test question {i}",
            type=QuestionDAO.get_question_type_for_user(test_user),
            level=1
        )
        await async_session.add(question)
    await async_session.commit()
    
    # Начинаем интервью
    start_response = await test_client.get("/interview/start", headers=auth_headers)
    interview_id = start_response.json()["id"]
    
    # Получаем вопрос
    question_response = await test_client.get(f"/interview/{interview_id}/question", headers=auth_headers)
    question_id = question_response.json()["id"]
    
    # Отправляем ответ на вопрос
    answer_data = {
        "interview_id": interview_id,
        "question_id": question_id,
        "text": "This is my test answer"
    }
    
    response = await test_client.post("/interview/answer", json=answer_data, headers=auth_headers)
    
    # Проверяем ответ
    assert response.status_code == 200
    data = response.json()
    assert "id" in data
    assert "feedback" in data
    assert "score" in data


@pytest.mark.asyncio
async def test_finish_interview(
    test_client: AsyncClient, 
    async_session: AsyncSession, 
    test_user: User, 
    auth_headers: dict
):
    """Тест завершения интервью"""
    # Создаем тестовые вопросы
    for i in range(15):
        question = Question(
            text=f"Test question {i}",
            type=QuestionDAO.get_question_type_for_user(test_user),
            level=1
        )
        await async_session.add(question)
    await async_session.commit()
    
    # Начинаем интервью
    start_response = await test_client.get("/interview/start", headers=auth_headers)
    interview_id = start_response.json()["id"]
    
    # Завершаем интервью
    response = await test_client.post(f"/interview/{interview_id}/finish", headers=auth_headers)
    
    # Проверяем ответ
    assert response.status_code == 200
    data = response.json()
    assert "id" in data
    assert "status" in data
    assert "score" in data
    assert data["status"] == "completed"
