import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession
from app.auth.models import User
import json


@pytest.mark.asyncio
async def test_register_user(test_client: AsyncClient, async_session: AsyncSession):
    """Тест регистрации пользователя"""
    # Данные для регистрации
    user_data = {
        "email": "new_user@example.com",
        "name": "New User",
    }
    
    # Отправляем запрос на регистрацию
    response = await test_client.post("/auth/register", json=user_data)
    
    # Проверяем ответ
    assert response.status_code == 200
    data = response.json()
    assert "id" in data
    assert data["email"] == user_data["email"]
    assert data["name"] == user_data["name"]
    
    # Проверяем наличие cookie с токеном
    assert "users_access_token" in response.cookies


@pytest.mark.asyncio
async def test_login_user(test_client: AsyncClient, test_user: User):
    """Тест авторизации пользователя"""
    # Данные для авторизации
    login_data = {
        "email": test_user.email,
    }
    
    # Отправляем запрос на авторизацию
    response = await test_client.post("/auth/login", json=login_data)
    
    # Проверяем ответ
    assert response.status_code == 200
    data = response.json()
    assert data["id"] == test_user.id
    assert data["email"] == test_user.email
    
    # Проверяем наличие cookie с токеном
    assert "users_access_token" in response.cookies


@pytest.mark.asyncio
async def test_get_current_user(test_client: AsyncClient, test_user: User, auth_headers: dict):
    """Тест получения информации о текущем пользователе"""
    # Отправляем запрос с токеном авторизации
    response = await test_client.get("/auth/me", headers=auth_headers)
    
    # Проверяем ответ
    assert response.status_code == 200
    data = response.json()
    assert data["id"] == test_user.id
    assert data["email"] == test_user.email
    assert data["name"] == test_user.name
    assert len(data["directions"]) > 0
    assert len(data["languages"]) > 0


@pytest.mark.asyncio
async def test_update_user(test_client: AsyncClient, test_user: User, auth_headers: dict):
    """Тест обновления данных пользователя"""
    # Данные для обновления
    update_data = {
        "name": "Updated User Name",
        "email": test_user.email,  # Email оставляем тем же
        "direction_ids": [direction.id for direction in test_user.directions],
        "language_ids": [language.id for language in test_user.languages],
    }
    
    # Отправляем запрос на обновление
    response = await test_client.put("/auth/update", json=update_data, headers=auth_headers)
    
    # Проверяем ответ
    assert response.status_code == 200
    data = response.json()
    assert data["name"] == update_data["name"]
    assert data["email"] == update_data["email"]


@pytest.mark.asyncio
async def test_email_check(test_client: AsyncClient, test_user: User):
    """Тест проверки существования email"""
    # Проверяем существующий email
    existing_email = {"email": test_user.email}
    response = await test_client.post("/auth/check_email", json=existing_email)
    assert response.status_code == 200
    data = response.json()
    assert data["exists"] is True
    
    # Проверяем несуществующий email
    non_existing_email = {"email": "nonexistent@example.com"}
    response = await test_client.post("/auth/check_email", json=non_existing_email)
    assert response.status_code == 200
    data = response.json()
    assert data["exists"] is False
