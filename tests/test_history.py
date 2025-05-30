import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession
from app.auth.models import User
from app.interview.models import Interview, Question, UserAnswer, InterviewStatus


@pytest.mark.asyncio
async def test_get_interview_history(
    test_client: AsyncClient, 
    async_session: AsyncSession, 
    test_user: User, 
    auth_headers: dict
):
    """Тест получения истории интервью"""
    # Создаем тестовое интервью
    interview = Interview(
        user_id=test_user.id,
        user_interview_id=1,
        status=InterviewStatus.COMPLETED,
        total_score=0.8
    )
    await async_session.add(interview)
    await async_session.commit()
    
    # Отправляем запрос на получение истории интервью
    response = await test_client.get("/history", headers=auth_headers)
    
    # Проверяем ответ
    assert response.status_code == 200
    data = response.json()
    assert "history" in data
    assert isinstance(data["history"], list)
    assert len(data["history"]) >= 1
    assert "id" in data["history"][0]
    assert "date" in data["history"][0]
    assert "score" in data["history"][0]


@pytest.mark.asyncio
async def test_get_interview_detail(
    test_client: AsyncClient, 
    async_session: AsyncSession, 
    test_user: User, 
    auth_headers: dict
):
    """Тест получения детальной информации об интервью"""
    # Создаем тестовое интервью
    interview = Interview(
        user_id=test_user.id,
        user_interview_id=1,
        status=InterviewStatus.COMPLETED,
        total_score=0.8
    )
    await async_session.add(interview)
    await async_session.flush()
    
    # Создаем тестовый вопрос
    question = Question(
        text="Test question",
        type="general",
        level=1
    )
    await async_session.add(question)
    await async_session.flush()
    
    # Создаем тестовый ответ
    user_answer = UserAnswer(
        interview_id=interview.id,
        question_id=question.id,
        text="Test answer",
        feedback="Test feedback",
        score=0.8
    )
    await async_session.add(user_answer)
    await async_session.commit()
    
    # Отправляем запрос на получение детальной информации об интервью
    response = await test_client.get(f"/history/{interview.user_interview_id}", headers=auth_headers)
    
    # Проверяем ответ
    assert response.status_code == 200
    data = response.json()
    assert "id" in data
    assert "date" in data
    assert "score" in data
    assert "questions" in data
    assert isinstance(data["questions"], list)
    assert len(data["questions"]) >= 1
    
    # Проверяем информацию о вопросе
    question_data = data["questions"][0]
    assert "text" in question_data
    assert "answer" in question_data
    assert "feedback" in question_data
    assert "score" in question_data
