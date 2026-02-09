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

router = APIRouter(prefix="/trade-offers", tags=["trade-offers"])


@router.get("", response_model=List[TradeOfferResponse])
def get_trade_offers(
    status_filter: Optional[TradeOfferStatus] = Query(None, description="Filter by offer status"),
    recipient_id_filter: Optional[int] = Query(None, alias="recipient_id", description="Filter by recipient user ID"),
    proposer_id_filter: Optional[int] = Query(None, alias="proposer_id", description="Filter by proposer user ID"),
    current_user: User = Depends(get_current_authenticated_user),
    db: Session = Depends(get_db)
):
    """
    Retrieve all trade offers for the authenticated user.

    Returns both offers where the user is the proposer (offers they made)
    and offers where the user is the recipient (offers they received).

    Can be filtered by status, recipient_id, or proposer_id.
    """
    # Build query to get offers where user is either proposer or recipient
    query = db.query(TradeOffer).filter(
        or_(
            TradeOffer.proposer_id == current_user.id,
            TradeOffer.recipient_id == current_user.id
        )
    )

    # Apply optional filters
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
    """
    Retrieve a specific trade offer by ID.

    Only accessible to users who are either the proposer or the recipient.
    """
    offer = db.query(TradeOffer).filter(TradeOffer.id == offer_id).first()

    if not offer:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Trade offer not found"
        )

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
    Create a new trade offer.

    The authenticated user (proposer) offers to exchange one of their games
    for a game owned by another user (recipient).

    Validation rules:
    - Cannot create an offer for yourself
    - The offered game must be owned by the authenticated user
    - The requested game must be owned by the recipient
    - No duplicate pending offers for the same game pair
    """
    requested_game = db.query(Game).filter(Game.id == offer_data.requested_game_id).first()
    if not requested_game:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Requested game not found"
        )

    recipient = db.query(User).filter(User.id == offer_data.recipient_id).first()
    if not recipient:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Recipient user not found"
        )

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

    # Find a game owned by the current user to offer
    # For this implementation, we'll use the first game owned by the user
    # In production, the client would specify which game to offer
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
    Respond to a trade offer (accept or reject).

    Only the recipient of the offer can respond to it.
    The offer must be in PENDING status to be responded to.

    Valid status transitions:
    - PENDING → ACCEPTED (recipient accepts)
    - PENDING → REJECTED (recipient rejects)
    """
    offer = db.query(TradeOffer).filter(TradeOffer.id == offer_id).first()

    if not offer:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Trade offer not found"
        )

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

    offer._links = build_trade_offer_links(offer.id)
    return offer


@router.delete("/{offer_id}", status_code=status.HTTP_204_NO_CONTENT)
def cancel_trade_offer(
    offer_id: int,
    current_user: User = Depends(get_current_authenticated_user),
    db: Session = Depends(get_db)
):
    """
    Cancel a trade offer.

    Only the proposer (creator) of the offer can cancel it.
    The offer must be in PENDING status to be cancelled.
    """
    offer = db.query(TradeOffer).filter(TradeOffer.id == offer_id).first()

    if not offer:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Trade offer not found"
        )

    # Authorization: only the proposer can cancel their own offers
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
