import re
from typing import Self, List
from pydantic import BaseModel, ConfigDict, EmailStr, Field, field_validator, model_validator, computed_field


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


class SUserRegisterSimple(BaseModel):
    email: EmailStr
    password: str = Field(min_length=5, max_length=50, description="Password from 5 to 50 characters")
    name: str = Field(min_length=2, max_length=50, description="Name from 2 to 50 characters")
    phone: str = Field(min_length=10, max_length=15, description="Phone number from 10 to 15 characters")

    @field_validator('phone')
    def validate_phone(cls, v):
        if not v.replace('+', '').isdigit():
            raise ValueError('Phone number must contain only digits and optionally a plus sign')
        return v


class SUserRegister(BaseModel):
    email: EmailStr
    password: str = Field(min_length=5, max_length=50, description="Password from 5 to 50 characters")
    confirm_password: str = Field(min_length=5, max_length=50, description="Password confirmation")
    name: str = Field(min_length=2, max_length=50, description="Name from 2 to 50 characters")
    phone: str = Field(min_length=10, max_length=15, description="Phone number from 10 to 15 characters")
    direction_ids: List[int] = Field(description="List of direction IDs")
    language_ids: List[int] = Field(description="List of language IDs")

    @field_validator('phone')
    def validate_phone(cls, v):
        if not v.replace('+', '').isdigit():
            raise ValueError('Phone number must contain only digits and optionally a plus sign')
        return v

    @model_validator(mode="after")
    def check_password(self) -> Self:
        if self.password != self.confirm_password:
            raise ValueError("Passwords do not match")
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

    class Config:
        from_attributes = True
        populate_by_name = True


class SUserUpdate(BaseModel):
    name: str | None = Field(None, min_length=2, max_length=50, description="Name from 2 to 50 characters")
    email: EmailStr | None = Field(None, description="Email")
    direction_ids: List[int] | None = Field(None, description="List of direction IDs. Send empty list to remove all directions")
    language_ids: List[int] | None = Field(None, description="List of language IDs. Send empty list to remove all languages")

    @model_validator(mode="after")
    def check_at_least_one_field(self) -> Self:
        if all(v is None for v in [self.name, self.email, self.direction_ids, self.language_ids]):
            raise ValueError("At least one field must be provided for update")
        return self

    class Config:
        from_attributes = True
        populate_by_name = True


class UserMeResponse(BaseModel):
    name: str
    email: EmailStr
    direction_ids: List[int]
    language_ids: List[int]

    class Config:
        from_attributes = True
