from app.dao.base import BaseDAO
from app.auth.models import User, Direction, Language


class UsersDAO(BaseDAO):
    model = User


class DirectionsDAO(BaseDAO):
    model = Direction


class LanguagesDAO(BaseDAO):
    model = Language

