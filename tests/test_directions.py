import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession
from app.auth.models import User, Direction


@pytest.mark.asyncio
async def test_get_all_directions(test_client: AsyncClient, async_session: AsyncSession, test_user: User):
    """Тест получения всех направлений"""
    # Отправляем запрос на получение всех направлений
    response = await test_client.get("/directions/")
    
    # Проверяем ответ
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)
    assert len(data) >= 1  # Минимум должно быть направление, созданное для тестового пользователя
    assert "id" in data[0]
    assert "name" in data[0]


@pytest.mark.asyncio
async def test_create_direction(test_client: AsyncClient, async_session: AsyncSession, auth_headers: dict):
    """Тест создания нового направления"""
    # Данные для создания нового направления
    direction_data = {
        "name": "New Test Direction"
    }
    
    # Отправляем запрос на создание направления
    response = await test_client.post("/directions/", json=direction_data, headers=auth_headers)
    
    # Проверяем ответ
    assert response.status_code == 200
    data = response.json()
    assert data["name"] == direction_data["name"]
    assert "id" in data


@pytest.mark.asyncio
async def test_delete_direction(
    test_client: AsyncClient, 
    async_session: AsyncSession, 
    auth_headers: dict,
    test_user: User
):
    """Тест удаления направления"""
    # Создаем направление для удаления
    direction_data = {
        "name": "Direction For Deletion"
    }
    create_response = await test_client.post("/directions/", json=direction_data, headers=auth_headers)
    direction_id = create_response.json()["id"]
    
    # Отправляем запрос на удаление направления
    response = await test_client.delete(f"/directions/{direction_id}", headers=auth_headers)
    
    # Проверяем ответ
    assert response.status_code == 204
    
    # Проверяем, что направление больше не существует
    get_response = await test_client.get("/directions/")
    data = get_response.json()
    assert all(item["id"] != direction_id for item in data)
