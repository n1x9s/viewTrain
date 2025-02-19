import re
from typing import Self
from pydantic import BaseModel, ConfigDict, EmailStr, Field, field_validator, model_validator, computed_field
from app.auth.utils import get_password_hash


class EmailModel(BaseModel):
    email: EmailStr = Field(description="Email")
    model_config = ConfigDict(from_attributes=True)


class UserBase(EmailModel):
    name: str = Field(min_length=2, max_length=50, description="Name from 2 to 50 characters")



class SUserRegister(UserBase):
    password: str = Field(min_length=5, max_length=50, description="Password from 5 to 50 characters")
    confirm_password: str = Field(min_length=5, max_length=50, description="Password confirmation")

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
