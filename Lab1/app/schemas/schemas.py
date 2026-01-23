from pydantic import BaseModel, EmailStr, Field
from typing import Optional, Dict
from enum import Enum


class Condition(str, Enum):
    mint = "mint"
    good = "good"
    fair = "fair"
    poor = "poor"


# HATEOAS Links
class Links(BaseModel):
    self: str
    update: Optional[str] = None
    delete: Optional[str] = None
    owner: Optional[str] = None
    games: Optional[str] = None


# User Schemas
class UserBase(BaseModel):
    name: str
    email: EmailStr
    street_address: str


class UserCreate(UserBase):
    password: str


class UserUpdate(BaseModel):
    name: Optional[str] = None
    street_address: Optional[str] = None


class UserResponse(UserBase):
    id: int
    _links: Links

    class Config:
        from_attributes = True


# Game Schemas
class GameBase(BaseModel):
    name: str
    publisher: str
    year_published: int
    system: str
    condition: Condition
    previous_owners: Optional[int] = None


class GameCreate(GameBase):
    owner_id: int


class GameUpdate(BaseModel):
    name: Optional[str] = None
    publisher: Optional[str] = None
    year_published: Optional[int] = None
    system: Optional[str] = None
    condition: Optional[Condition] = None
    previous_owners: Optional[int] = None


class GameResponse(GameBase):
    id: int
    owner_id: int
    _links: Links

    class Config:
        from_attributes = True


# Error Schema
class Error(BaseModel):
    code: int
    message: str
    details: Optional[str] = None
