from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from typing import List, Optional

from app.database import get_db
from app.models import Game, User
from app.schemas.schemas import GameCreate, GameResponse, GameUpdate
from app.utils import build_game_links

router = APIRouter(prefix="/games", tags=["games"])


@router.get("", response_model=List[GameResponse])
def get_all_games(db: Session = Depends(get_db)):
    """Get all games"""
    games = db.query(Game).all()
    for game in games:
        game._links = build_game_links(game.id, game.owner_id)
    return games


@router.get("/search", response_model=List[GameResponse])
def search_games(
    name: Optional[str] = Query(None, description="Name of the game to search for"),
    publisher: Optional[str] = Query(None, description="Publisher to filter by"),
    system: Optional[str] = Query(None, description="Gaming system to filter by"),
    condition: Optional[str] = Query(None, description="Condition to filter by"),
    owner_id: Optional[int] = Query(None, description="Owner ID to filter by"),
    year_before: Optional[int] = Query(None, description="Filter games published before this year"),
    year_after: Optional[int] = Query(None, description="Filter games published after this year"),
    db: Session = Depends(get_db)
):
    """Search for games by various criteria"""
    query = db.query(Game)

    if name:
        query = query.filter(Game.name.ilike(f"%{name}%"))
    if publisher:
        query = query.filter(Game.publisher.ilike(f"%{publisher}%"))
    if system:
        query = query.filter(Game.system.ilike(f"%{system}%"))
    if condition:
        query = query.filter(Game.condition == condition)
    if owner_id is not None:
        query = query.filter(Game.owner_id == owner_id)
    if year_before is not None:
        query = query.filter(Game.year_published < year_before)
    if year_after is not None:
        query = query.filter(Game.year_published > year_after)

    games = query.all()
    for game in games:
        game._links = build_game_links(game.id, game.owner_id)
    return games


@router.post("", response_model=GameResponse, status_code=status.HTTP_201_CREATED)
def create_game(game: GameCreate, db: Session = Depends(get_db)):
    """Add a new game to the exchange list"""
    # Verify owner exists
    owner = db.query(User).filter(User.id == game.owner_id).first()
    if not owner:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Owner not found"
        )

    db_game = Game(
        name=game.name,
        publisher=game.publisher,
        year_published=game.year_published,
        system=game.system,
        condition=game.condition,
        previous_owners=game.previous_owners,
        owner_id=game.owner_id
    )
    db.add(db_game)
    db.commit()
    db.refresh(db_game)

    db_game._links = build_game_links(db_game.id, db_game.owner_id)
    return db_game


@router.get("/{game_id}", response_model=GameResponse)
def get_game(game_id: int, db: Session = Depends(get_db)):
    """Get a specific game by ID"""
    game = db.query(Game).filter(Game.id == game_id).first()
    if not game:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Game not found"
        )
    game._links = build_game_links(game.id, game.owner_id)
    return game


@router.put("/{game_id}", response_model=GameResponse)
def replace_game(game_id: int, game: GameCreate, db: Session = Depends(get_db)):
    """Replace all properties of a game"""
    db_game = db.query(Game).filter(Game.id == game_id).first()
    if not db_game:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Game not found"
        )

    # Verify owner exists
    owner = db.query(User).filter(User.id == game.owner_id).first()
    if not owner:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Owner not found"
        )

    db_game.name = game.name
    db_game.publisher = game.publisher
    db_game.year_published = game.year_published
    db_game.system = game.system
    db_game.condition = game.condition
    db_game.previous_owners = game.previous_owners
    db_game.owner_id = game.owner_id
    db.commit()
    db.refresh(db_game)

    db_game._links = build_game_links(db_game.id, db_game.owner_id)
    return db_game


@router.patch("/{game_id}", response_model=GameResponse)
def update_game(game_id: int, game: GameUpdate, db: Session = Depends(get_db)):
    """Partially update a game"""
    db_game = db.query(Game).filter(Game.id == game_id).first()
    if not db_game:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Game not found"
        )

    if game.name is not None:
        db_game.name = game.name
    if game.publisher is not None:
        db_game.publisher = game.publisher
    if game.year_published is not None:
        db_game.year_published = game.year_published
    if game.system is not None:
        db_game.system = game.system
    if game.condition is not None:
        db_game.condition = game.condition
    if game.previous_owners is not None:
        db_game.previous_owners = game.previous_owners

    db.commit()
    db.refresh(db_game)

    db_game._links = build_game_links(db_game.id, db_game.owner_id)
    return db_game


@router.delete("/{game_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_game(game_id: int, db: Session = Depends(get_db)):
    """Delete a game"""
    db_game = db.query(Game).filter(Game.id == game_id).first()
    if not db_game:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Game not found"
        )
    db.delete(db_game)
    db.commit()
    return None
