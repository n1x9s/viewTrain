from typing import List
from fastapi import APIRouter, Response, Depends, HTTPException, status
from app.auth.dependencies import get_current_user #, get_current_admin_user
from app.auth.models import User, Direction, Language
from app.exceptions import UserAlreadyExistsException, IncorrectEmailOrPasswordException
from app.auth.auth import authenticate_user, create_access_token
from app.auth.dao import UsersDAO, DirectionsDAO, LanguagesDAO
from app.auth.schemas import SUserRegister, SUserAuth, EmailModel, SUserAddDB, SUserInfo, DirectionSchema, LanguageSchema, DirectionCreate, LanguageCreate
from sqlalchemy.ext.asyncio import AsyncSession
from pydantic import BaseModel

from app.dao.session_maker import TransactionSessionDep, SessionDep

router = APIRouter(prefix='/auth', tags=['Auth'])


class IdModel(BaseModel):
    id: int


@router.post("/register/")
async def register_user(user_data: SUserRegister, session: AsyncSession = TransactionSessionDep) -> dict:
    # Проверяем, существует ли пользователь с таким email
    user = await UsersDAO.find_one_or_none(session=session, filters=EmailModel(email=user_data.email))
    if user:
        raise UserAlreadyExistsException
    
    # Проверяем, существуют ли выбранные направления
    directions = await DirectionsDAO.find_by_ids(session=session, ids=user_data.direction_ids)
    if len(directions) != len(user_data.direction_ids):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="One or more selected directions do not exist"
        )
    
    # Проверяем, существуют ли выбранные языки
    languages = await LanguagesDAO.find_by_ids(session=session, ids=user_data.language_ids)
    if len(languages) != len(user_data.language_ids):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="One or more selected languages do not exist"
        )
    
    # Создаем пользователя только с основными полями
    user_data_dict = {
        "email": user_data.email,
        "name": user_data.name,
        "password": user_data.password,
        "directions": directions,
        "languages": languages
    }
    
    # Создаем нового пользователя
    new_user = User(**user_data_dict)
    session.add(new_user)
    await session.commit()
    
    return {'message': f'Registration is successful!'}


@router.post("/login/")
async def auth_user(response: Response, user_data: SUserAuth, session: AsyncSession = SessionDep):
    check = await authenticate_user(session=session, email=user_data.email, password=user_data.password)
    if check is None:
        raise IncorrectEmailOrPasswordException
    access_token = create_access_token({"sub": str(check.id)})
    response.set_cookie(key="users_access_token", value=access_token, httponly=True)
    return {'ok': True, 'access_token': access_token, 'message': 'Authorization is successful!'}


@router.post("/logout/")
async def logout_user(response: Response):
    response.delete_cookie(key="users_access_token")
    return {'message': 'Logout is successful!'}


@router.get("/me/")
async def get_me(user_data: User = Depends(get_current_user)) -> SUserInfo:
    return SUserInfo.model_validate(user_data)


@router.get("/directions/", response_model=List[DirectionSchema])
async def get_directions(session: AsyncSession = SessionDep):
    directions = await DirectionsDAO.find_all(session=session, filters=None)
    return directions


@router.post("/directions/", response_model=DirectionSchema, status_code=status.HTTP_201_CREATED)
async def create_direction(
    direction_data: DirectionCreate, 
    session: AsyncSession = TransactionSessionDep,
    current_user: User = Depends(get_current_user)
):
    # Проверяем, существует ли уже такое направление
    existing = await DirectionsDAO.find_one_or_none(
        session=session, 
        filters=DirectionCreate(name=direction_data.name)
    )
    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Direction with name '{direction_data.name}' already exists"
        )
    
    # Создаем новое направление
    new_direction = await DirectionsDAO.add(session=session, values=direction_data)
    return new_direction


@router.delete("/directions/{direction_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_direction(
    direction_id: int,
    session: AsyncSession = TransactionSessionDep,
    current_user: User = Depends(get_current_user)
):
    # Проверяем, существует ли направление
    direction = await DirectionsDAO.find_one_or_none_by_id(data_id=direction_id, session=session)
    if not direction:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Direction with ID {direction_id} not found"
        )
    
    # Удаляем направление
    await DirectionsDAO.delete(session=session, filters=IdModel(id=direction_id))
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.get("/languages/", response_model=List[LanguageSchema])
async def get_languages(session: AsyncSession = SessionDep):
    languages = await LanguagesDAO.find_all(session=session, filters=None)
    return languages


@router.post("/languages/", response_model=LanguageSchema, status_code=status.HTTP_201_CREATED)
async def create_language(
    language_data: LanguageCreate, 
    session: AsyncSession = TransactionSessionDep,
    current_user: User = Depends(get_current_user)
):
    # Проверяем, существует ли уже такой язык
    existing = await LanguagesDAO.find_one_or_none(
        session=session, 
        filters=LanguageCreate(name=language_data.name)
    )
    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Language with name '{language_data.name}' already exists"
        )
    
    # Создаем новый язык
    new_language = await LanguagesDAO.add(session=session, values=language_data)
    return new_language


@router.delete("/languages/{language_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_language(
    language_id: int,
    session: AsyncSession = TransactionSessionDep,
    current_user: User = Depends(get_current_user)
):
    # Проверяем, существует ли язык
    language = await LanguagesDAO.find_one_or_none_by_id(data_id=language_id, session=session)
    if not language:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Language with ID {language_id} not found"
        )
    
    # Удаляем язык
    await LanguagesDAO.delete(session=session, filters=IdModel(id=language_id))
    return Response(status_code=status.HTTP_204_NO_CONTENT)


# @router.get("/all_users/")
# async def get_all_users(session: AsyncSession = SessionDep,
#                         user_data: User = Depends(get_current_admin_user)) -> List[SUserInfo]:
#     return await UsersDAO.find_all(session=session, filters=None)
