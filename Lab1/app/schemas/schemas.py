from pydantic import BaseModel, EmailStr, Field
from typing import Optional, Dict
from enum import Enum
from datetime import datetime


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


# Trade Offer Schemas
class TradeOfferStatus(str, Enum):
    """Enumeration of possible states for a trade offer"""
    PENDING = "pending"
    ACCEPTED = "accepted"
    REJECTED = "rejected"
    CANCELLED = "cancelled"


class TradeOfferBase(BaseModel):
    """Base fields for a trade offer"""
    message: Optional[str] = None


class TradeOfferCreate(TradeOfferBase):
    """
    Schema for creating a new trade offer.

    The offered_game_id is determined from the authenticated user's owned games.
    The requester specifies which game they want and who they want to trade with.
    """
    requested_game_id: int = Field(..., description="ID of the game the proposer wants to receive")
    recipient_id: int = Field(..., description="ID of the user who owns the requested game")


class TradeOfferUpdate(BaseModel):
    """
    Schema for updating a trade offer (responding to an offer).

    Only the recipient can change the status to ACCEPTED or REJECTED.
    Only the proposer can change the status to CANCELLED (while still pending).
    """
    status: TradeOfferStatus


class TradeOfferResponse(TradeOfferBase):
    """Schema for trade offer responses with HATEOAS links"""
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
