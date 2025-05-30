import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession
from app.auth.models import User, Language


@pytest.mark.asyncio
async def test_get_all_languages(test_client: AsyncClient, async_session: AsyncSession, test_user: User):
    """Тест получения всех языков программирования"""
    # Отправляем запрос на получение всех языков
    response = await test_client.get("/languages/")
    
    # Проверяем ответ
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)
    assert len(data) >= 1  # Минимум должен быть язык, созданный для тестового пользователя
    assert "id" in data[0]
    assert "name" in data[0]


@pytest.mark.asyncio
async def test_create_language(test_client: AsyncClient, async_session: AsyncSession, auth_headers: dict):
    """Тест создания нового языка программирования"""
    # Данные для создания нового языка
    language_data = {
        "name": "New Test Language"
    }
    
    # Отправляем запрос на создание языка
    response = await test_client.post("/languages/", json=language_data, headers=auth_headers)
    
    # Проверяем ответ
    assert response.status_code == 200
    data = response.json()
    assert data["name"] == language_data["name"]
    assert "id" in data


@pytest.mark.asyncio
async def test_delete_language(
    test_client: AsyncClient, 
    async_session: AsyncSession, 
    auth_headers: dict,
    test_user: User
):
    """Тест удаления языка программирования"""
    # Создаем язык для удаления
    language_data = {
        "name": "Language For Deletion"
    }
    create_response = await test_client.post("/languages/", json=language_data, headers=auth_headers)
    language_id = create_response.json()["id"]
    
    # Отправляем запрос на удаление языка
    response = await test_client.delete(f"/languages/{language_id}", headers=auth_headers)
    
    # Проверяем ответ
    assert response.status_code == 204
    
    # Проверяем, что язык больше не существует
    get_response = await test_client.get("/languages/")
    data = get_response.json()
    assert all(item["id"] != language_id for item in data)
