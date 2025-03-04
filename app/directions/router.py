from typing import List
from fastapi import APIRouter, Response, Depends, HTTPException, status
from app.auth.dependencies import get_current_user
from app.auth.models import User
from app.auth.dao import DirectionsDAO
from app.auth.schemas import DirectionSchema, DirectionCreate
from sqlalchemy.ext.asyncio import AsyncSession
from pydantic import BaseModel

from app.dao.session_maker import TransactionSessionDep, SessionDep

router = APIRouter(prefix='/directions', tags=['Directions'])


class IdModel(BaseModel):
    id: int


@router.get("/", response_model=List[DirectionSchema])
async def get_directions(session: AsyncSession = SessionDep):
    directions = await DirectionsDAO.find_all(session=session, filters=None)
    return directions


@router.post("/", response_model=DirectionSchema, status_code=status.HTTP_201_CREATED)
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


@router.delete("/{direction_id}", status_code=status.HTTP_204_NO_CONTENT)
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