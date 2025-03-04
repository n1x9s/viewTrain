from typing import List
from fastapi import APIRouter, Response, Depends, HTTPException, status
from app.auth.dependencies import get_current_user
from app.auth.models import User
from app.auth.dao import LanguagesDAO
from app.auth.schemas import LanguageSchema, LanguageCreate
from sqlalchemy.ext.asyncio import AsyncSession
from pydantic import BaseModel

from app.dao.session_maker import TransactionSessionDep, SessionDep

router = APIRouter(prefix='/languages', tags=['Languages'])


class IdModel(BaseModel):
    id: int


@router.get("/", response_model=List[LanguageSchema])
async def get_languages(session: AsyncSession = SessionDep):
    languages = await LanguagesDAO.find_all(session=session, filters=None)
    return languages


@router.post("/", response_model=LanguageSchema, status_code=status.HTTP_201_CREATED)
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


@router.delete("/{language_id}", status_code=status.HTTP_204_NO_CONTENT)
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