from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List

from app.database import get_db
from app.models import User
from app.schemas.schemas import UserCreate, UserResponse, UserUpdate, Error
from app.utils import build_user_links

router = APIRouter(prefix="/users", tags=["users"])


@router.get("", response_model=List[UserResponse])
def get_all_users(db: Session = Depends(get_db)):
    """Get all users"""
    users = db.query(User).all()
    for user in users:
        user._links = build_user_links(user.id)
    return users


@router.post("", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
def create_user(user: UserCreate, db: Session = Depends(get_db)):
    """Create a new user"""
    # Check if email already exists
    existing_user = db.query(User).filter(User.email == user.email).first()
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already registered"
        )

    # Hash password (in production, use bcrypt/passlib)
    # For now, storing as-is for the lab
    db_user = User(
        name=user.name,
        email=user.email,
        password=user.password,  # TODO: Hash this in production
        street_address=user.street_address
    )
    db.add(db_user)
    db.commit()
    db.refresh(db_user)

    db_user._links = build_user_links(db_user.id)
    return db_user


@router.get("/{user_id}", response_model=UserResponse)
def get_user(user_id: int, db: Session = Depends(get_db)):
    """Get a specific user by ID"""
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    user._links = build_user_links(user.id)
    return user


@router.put("/{user_id}", response_model=UserResponse)
def replace_user(user_id: int, user: UserCreate, db: Session = Depends(get_db)):
    """Replace all properties of a user"""
    db_user = db.query(User).filter(User.id == user_id).first()
    if not db_user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )

    # Check if new email conflicts with another user
    existing_user = db.query(User).filter(
        User.email == user.email,
        User.id != user_id
    ).first()
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already in use by another user"
        )

    db_user.name = user.name
    db_user.email = user.email
    db_user.password = user.password  # TODO: Hash in production
    db_user.street_address = user.street_address
    db.commit()
    db.refresh(db_user)

    db_user._links = build_user_links(db_user.id)
    return db_user


@router.patch("/{user_id}", response_model=UserResponse)
def update_user(user_id: int, user: UserUpdate, db: Session = Depends(get_db)):
    """Partially update a user (name and street address only - email is immutable)"""
    db_user = db.query(User).filter(User.id == user_id).first()
    if not db_user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )

    if user.name is not None:
        db_user.name = user.name
    if user.street_address is not None:
        db_user.street_address = user.street_address

    db.commit()
    db.refresh(db_user)

    db_user._links = build_user_links(db_user.id)
    return db_user


@router.delete("/{user_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_user(user_id: int, db: Session = Depends(get_db)):
    """Delete a user"""
    db_user = db.query(User).filter(User.id == user_id).first()
    if not db_user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    db.delete(db_user)
    db.commit()
    return None
