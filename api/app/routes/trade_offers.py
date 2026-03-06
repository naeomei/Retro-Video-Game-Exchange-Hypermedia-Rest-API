# =============================================================================
# routes/trade_offers.py — Trade Offer Endpoints
# =============================================================================
# What this file does:
#   Manages the core business logic of the exchange: creating offers, viewing
#   them, responding (accept/reject), and cancelling. All endpoints require
#   authentication — users can only see and act on offers they're part of.
#
# Key decisions:
#   - Auth on every route: trade offers are private, not publicly browsable.
#   - Role-based restrictions: only the recipient can accept/reject, only the
#     proposer can cancel. Enforced at the route level with explicit checks.
#   - Kafka events on state changes: email notifications are decoupled from the
#     API — we publish the event and the email service handles delivery async.
#   - Offered game auto-selection: picks the proposer's first game. A production
#     app would let the client specify which of their games to offer.
#
# State machine: PENDING → ACCEPTED | REJECTED | CANCELLED (all terminal)
# =============================================================================

from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from sqlalchemy import or_
from typing import List, Optional
from datetime import datetime

from app.database import get_db
from app.models import User, Game, TradeOffer, TradeOfferStatus
from app.schemas.schemas import TradeOfferCreate, TradeOfferResponse, TradeOfferUpdate
from app.utils import build_trade_offer_links
from app.auth import get_current_authenticated_user
from app.kafka_producer import publish_notification_event

router = APIRouter(prefix="/trade-offers", tags=["trade-offers"])


@router.get("", response_model=List[TradeOfferResponse])
def get_trade_offers(
    status_filter: Optional[TradeOfferStatus] = Query(None, description="Filter by offer status"),
    recipient_id_filter: Optional[int] = Query(None, alias="recipient_id", description="Filter by recipient user ID"),
    proposer_id_filter: Optional[int] = Query(None, alias="proposer_id", description="Filter by proposer user ID"),
    current_user: User = Depends(get_current_authenticated_user),
    db: Session = Depends(get_db)
):
    """Returns all offers where the authenticated user is the proposer or recipient."""
    query = db.query(TradeOffer).filter(
        or_(
            TradeOffer.proposer_id == current_user.id,
            TradeOffer.recipient_id == current_user.id
        )
    )

    if status_filter:
        query = query.filter(TradeOffer.status == status_filter)
    if recipient_id_filter:
        query = query.filter(TradeOffer.recipient_id == recipient_id_filter)
    if proposer_id_filter:
        query = query.filter(TradeOffer.proposer_id == proposer_id_filter)

    offers = query.order_by(TradeOffer.created_at.desc()).all()
    for offer in offers:
        offer._links = build_trade_offer_links(offer.id)
    return offers


@router.get("/{offer_id}", response_model=TradeOfferResponse)
def get_trade_offer(
    offer_id: int,
    current_user: User = Depends(get_current_authenticated_user),
    db: Session = Depends(get_db)
):
    """Only the proposer or recipient can view a specific offer."""
    offer = db.query(TradeOffer).filter(TradeOffer.id == offer_id).first()
    if not offer:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Trade offer not found")

    if current_user.id != offer.proposer_id and current_user.id != offer.recipient_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You are not authorized to view this trade offer"
        )

    offer._links = build_trade_offer_links(offer.id)
    return offer


@router.post("", response_model=TradeOfferResponse, status_code=status.HTTP_201_CREATED)
def create_trade_offer(
    offer_data: TradeOfferCreate,
    current_user: User = Depends(get_current_authenticated_user),
    db: Session = Depends(get_db)
):
    """
    Create a trade offer. The authenticated user is the proposer.
    Their first owned game is auto-selected as the offered game.
    Can't trade with yourself, both games must exist and be owned by the right
    users, and no duplicate pending offers for the same game pair are allowed.
    """
    requested_game = db.query(Game).filter(Game.id == offer_data.requested_game_id).first()
    if not requested_game:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Requested game not found")

    recipient = db.query(User).filter(User.id == offer_data.recipient_id).first()
    if not recipient:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Recipient user not found")

    if requested_game.owner_id != offer_data.recipient_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Requested game is not owned by the specified recipient"
        )

    if current_user.id == offer_data.recipient_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot create a trade offer for yourself"
        )

    # Auto-select the proposer's first game. In production the client would
    # specify which of their games to put up for trade.
    users_games = db.query(Game).filter(Game.owner_id == current_user.id).all()
    if not users_games:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="You must own at least one game to create a trade offer"
        )

    offered_game = users_games[0]

    existing_offer = db.query(TradeOffer).filter(
        TradeOffer.proposer_id == current_user.id,
        TradeOffer.recipient_id == offer_data.recipient_id,
        TradeOffer.offered_game_id == offered_game.id,
        TradeOffer.requested_game_id == offer_data.requested_game_id,
        TradeOffer.status == TradeOfferStatus.PENDING
    ).first()

    if existing_offer:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="A pending trade offer for these games already exists"
        )

    new_offer = TradeOffer(
        proposer_id=current_user.id,
        recipient_id=offer_data.recipient_id,
        offered_game_id=offered_game.id,
        requested_game_id=offer_data.requested_game_id,
        status=TradeOfferStatus.PENDING,
        message=offer_data.message
    )

    db.add(new_offer)
    db.commit()
    db.refresh(new_offer)

    publish_notification_event(
        event_type='trade_offer_created',
        data={
            'offer_id': new_offer.id,
            'offeror_id': new_offer.proposer_id,
            'offeror_email': current_user.email,
            'offeror_name': current_user.name,
            'offeree_id': new_offer.recipient_id,
            'offeree_email': recipient.email,
            'offeree_name': recipient.name,
            'offered_game_name': offered_game.name,
            'requested_game_name': requested_game.name,
            'message': new_offer.message or ''
        }
    )

    new_offer._links = build_trade_offer_links(new_offer.id)
    return new_offer


@router.patch("/{offer_id}", response_model=TradeOfferResponse)
def respond_to_trade_offer(
    offer_id: int,
    update_data: TradeOfferUpdate,
    current_user: User = Depends(get_current_authenticated_user),
    db: Session = Depends(get_db)
):
    """
    Accept or reject a pending offer. Only the recipient can respond.
    Valid transitions: PENDING → ACCEPTED or PENDING → REJECTED.
    """
    offer = db.query(TradeOffer).filter(TradeOffer.id == offer_id).first()
    if not offer:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Trade offer not found")

    if current_user.id != offer.recipient_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only the recipient can respond to this trade offer"
        )

    if offer.status != TradeOfferStatus.PENDING:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Cannot respond to an offer with status: {offer.status.value}"
        )

    if update_data.status not in [TradeOfferStatus.ACCEPTED, TradeOfferStatus.REJECTED]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Recipients can only accept or reject offers"
        )

    offer.status = update_data.status
    offer.responded_at = datetime.utcnow()
    db.commit()
    db.refresh(offer)

    event_type = 'trade_offer_accepted' if update_data.status == TradeOfferStatus.ACCEPTED else 'trade_offer_rejected'
    publish_notification_event(
        event_type=event_type,
        data={
            'offer_id': offer.id,
            'offeror_id': offer.proposer_id,
            'offeror_email': offer.proposer.email,
            'offeror_name': offer.proposer.name,
            'offeree_id': offer.recipient_id,
            'offeree_email': offer.recipient.email,
            'offeree_name': offer.recipient.name,
            'offered_game_name': offer.offered_game.name,
            'requested_game_name': offer.requested_game.name,
            'responded_at': offer.responded_at.isoformat() + 'Z'
        }
    )

    offer._links = build_trade_offer_links(offer.id)
    return offer


@router.delete("/{offer_id}", status_code=status.HTTP_204_NO_CONTENT)
def cancel_trade_offer(
    offer_id: int,
    current_user: User = Depends(get_current_authenticated_user),
    db: Session = Depends(get_db)
):
    """Cancel a pending offer. Only the proposer can cancel."""
    offer = db.query(TradeOffer).filter(TradeOffer.id == offer_id).first()
    if not offer:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Trade offer not found")

    if current_user.id != offer.proposer_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only the proposer can cancel this trade offer"
        )

    if offer.status != TradeOfferStatus.PENDING:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Cannot cancel an offer with status: {offer.status.value}"
        )

    offer.status = TradeOfferStatus.CANCELLED
    db.commit()
    return None
