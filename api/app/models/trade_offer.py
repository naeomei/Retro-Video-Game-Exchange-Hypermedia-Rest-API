# =============================================================================
# models/trade_offer.py — Trade Offer Database Model
# =============================================================================
# What this file does:
#   Defines the SQLAlchemy model for trade offers and the status enum that
#   drives the state machine. A trade offer connects two users and two games.
#
# Key decisions:
#   - SQLEnum stored in DB: status is stored as a proper enum type, not a plain
#     string — the database rejects any value not in the enum.
#   - onupdate=datetime.utcnow on updated_at: SQLAlchemy sets this automatically
#     on every UPDATE without needing any manual code in the route handlers.
#   - Multiple FK relationships to User: both proposer and recipient are users.
#     SQLAlchemy needs explicit foreign_keys=[...] hints when there are multiple
#     foreign keys pointing to the same table, otherwise it can't tell which
#     relationship maps to which key.
#
# State machine: PENDING → ACCEPTED | REJECTED | CANCELLED (all terminal)
# =============================================================================

from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Enum as SQLEnum, Text
from sqlalchemy.orm import relationship
from app.database import Base
from datetime import datetime
import enum


class TradeOfferStatus(str, enum.Enum):
    PENDING = "pending"
    ACCEPTED = "accepted"
    REJECTED = "rejected"
    CANCELLED = "cancelled"


class TradeOffer(Base):
    __tablename__ = "trade_offers"

    id = Column(Integer, primary_key=True, index=True)
    proposer_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    recipient_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    offered_game_id = Column(Integer, ForeignKey("games.id"), nullable=False, index=True)
    requested_game_id = Column(Integer, ForeignKey("games.id"), nullable=False, index=True)
    status = Column(SQLEnum(TradeOfferStatus), default=TradeOfferStatus.PENDING, nullable=False, index=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    responded_at = Column(DateTime, nullable=True)
    message = Column(Text, nullable=True)

    proposer = relationship("User", foreign_keys=[proposer_id], backref="proposed_trade_offers")
    recipient = relationship("User", foreign_keys=[recipient_id], backref="received_trade_offers")
    offered_game = relationship("Game", foreign_keys=[offered_game_id])
    requested_game = relationship("Game", foreign_keys=[requested_game_id])
