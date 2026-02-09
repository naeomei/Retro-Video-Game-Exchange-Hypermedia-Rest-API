from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Enum as SQLEnum, Text
from sqlalchemy.orm import relationship
from app.database import Base
from datetime import datetime
import enum


class TradeOfferStatus(str, enum.Enum):
    """
    Enumeration of possible states for a trade offer.

    State Machine Flow:
    - pending → accepted (when recipient accepts)
    - pending → rejected (when recipient rejects)
    - pending → cancelled (when proposer cancels)

    Terminal states: accepted, rejected, cancelled
    """
    PENDING = "pending"
    ACCEPTED = "accepted"
    REJECTED = "rejected"
    CANCELLED = "cancelled"


class TradeOffer(Base):
    """
    Database model representing a trade offer between two users.

    A trade offer represents a proposal where one user offers to exchange
    one of their games for a game owned by another user.

    State Transitions:
    - Created in PENDING state
    - Recipient can accept or reject (changes to ACCEPTED or REJECTED)
    - Proposer can cancel while still pending (changes to CANCELLED)
    """
    __tablename__ = "trade_offers"

    id = Column(Integer, primary_key=True, index=True)

    proposer_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)

    recipient_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)

    offered_game_id = Column(Integer, ForeignKey("games.id"), nullable=False, index=True)

    requested_game_id = Column(Integer, ForeignKey("games.id"), nullable=False, index=True)

    status = Column(
        SQLEnum(TradeOfferStatus),
        default=TradeOfferStatus.PENDING,
        nullable=False,
        index=True
    )

    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    responded_at = Column(DateTime, nullable=True)

    message = Column(Text, nullable=True)

    proposer = relationship("User", foreign_keys=[proposer_id], backref="proposed_trade_offers")

    recipient = relationship("User", foreign_keys=[recipient_id], backref="received_trade_offers")

    offered_game = relationship("Game", foreign_keys=[offered_game_id])

    requested_game = relationship("Game", foreign_keys=[requested_game_id])
