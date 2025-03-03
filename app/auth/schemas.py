import re
from typing import Self, List
from pydantic import BaseModel, ConfigDict, EmailStr, Field, field_validator, model_validator, computed_field
from app.auth.utils import get_password_hash


class EmailModel(BaseModel):
    email: EmailStr = Field(description="Email")
    model_config = ConfigDict(from_attributes=True)


class UserBase(EmailModel):
    name: str = Field(min_length=2, max_length=50, description="Name from 2 to 50 characters")


class DirectionSchema(BaseModel):
    id: int = Field(description="Direction ID")
    name: str = Field(description="Direction name")
    model_config = ConfigDict(from_attributes=True)


class DirectionCreate(BaseModel):
    name: str = Field(min_length=2, max_length=50, description="Direction name")


class LanguageSchema(BaseModel):
    id: int = Field(description="Language ID")
    name: str = Field(description="Language name")
    model_config = ConfigDict(from_attributes=True)


class LanguageCreate(BaseModel):
    name: str = Field(min_length=2, max_length=50, description="Language name")


class SUserRegister(UserBase):
    password: str = Field(min_length=5, max_length=50, description="Password from 5 to 50 characters")
    confirm_password: str = Field(min_length=5, max_length=50, description="Password confirmation")
    direction_ids: List[int] = Field(description="List of direction IDs")
    language_ids: List[int] = Field(description="List of language IDs")

    @model_validator(mode="after")
    def check_password(self) -> Self:
        if self.password != self.confirm_password:
            raise ValueError("Passwords do not match")
        self.password = get_password_hash(self.password)
        return self


class SUserAddDB(UserBase):
    password: str = Field(min_length=5, description="Hashed password")


class SUserAuth(EmailModel):
    password: str = Field(min_length=5, max_length=50, description="Password from 5 to 50 characters")


# class RoleModel(BaseModel):
#     id: int = Field(description="Role ID")
#     name: str = Field(description="Role name")
#     model_config = ConfigDict(from_attributes=True)


class SUserInfo(UserBase):
    id: int = Field(description="User ID")
    directions: List[DirectionSchema] = Field(default_factory=list, description="User directions")
    languages: List[LanguageSchema] = Field(default_factory=list, description="User languages")
