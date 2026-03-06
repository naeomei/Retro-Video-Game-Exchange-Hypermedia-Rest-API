# =============================================================================
# schemas/schemas.py — Pydantic Request/Response Schemas
# =============================================================================
# What this file does:
#   Defines the shape of data coming in (requests) and going out (responses)
#   for every resource: Users, Games, and Trade Offers. Pydantic validates
#   incoming JSON automatically — if the shape doesn't match, FastAPI returns
#   a 422 error before the route function even runs.
#
# Key decisions:
#   - Separate Base/Create/Update/Response classes per resource: Base holds
#     shared fields, Create adds write-only fields (like password), Update makes
#     fields Optional for PATCH support, Response adds read-only fields (id, links).
#   - HATEOAS _links on every response: each resource tells the client what
#     actions are available next, following REST level 3 maturity.
#   - from_attributes = True (formerly orm_mode): tells Pydantic to read data
#     from SQLAlchemy model attributes instead of requiring a plain dict.
# =============================================================================

from pydantic import BaseModel, EmailStr, Field
from typing import Optional, Dict
from enum import Enum
from datetime import datetime
from app.models import TradeOfferStatus


class Condition(str, Enum):
    mint = "mint"
    good = "good"
    fair = "fair"
    poor = "poor"


class Links(BaseModel):
    self: str
    update: Optional[str] = None
    delete: Optional[str] = None
    owner: Optional[str] = None
    games: Optional[str] = None


class UserBase(BaseModel):
    name: str
    email: EmailStr
    street_address: str


class UserCreate(UserBase):
    password: str


class UserUpdate(BaseModel):
    name: Optional[str] = None
    street_address: Optional[str] = None
    password: Optional[str] = None


class UserResponse(UserBase):
    id: int
    _links: Links

    class Config:
        from_attributes = True


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


class Error(BaseModel):
    code: int
    message: str
    details: Optional[str] = None


class TradeOfferBase(BaseModel):
    message: Optional[str] = None


class TradeOfferCreate(TradeOfferBase):
    # The proposer only specifies what they want and who has it.
    # Which of their own games to offer is auto-selected server-side.
    requested_game_id: int = Field(..., description="ID of the game the proposer wants to receive")
    recipient_id: int = Field(..., description="ID of the user who owns the requested game")


class TradeOfferUpdate(BaseModel):
    # Recipients set ACCEPTED or REJECTED. Proposers set CANCELLED.
    # The route layer enforces who can set which status.
    status: TradeOfferStatus


class TradeOfferResponse(TradeOfferBase):
    id: int
    proposer_id: int
    recipient_id: int
    offered_game_id: int
    requested_game_id: int
    status: TradeOfferStatus
    created_at: datetime
    updated_at: datetime
    responded_at: Optional[datetime] = None
    _links: Links

    class Config:
        from_attributes = True
