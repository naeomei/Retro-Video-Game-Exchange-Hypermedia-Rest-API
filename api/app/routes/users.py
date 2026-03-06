# =============================================================================
# routes/users.py — User CRUD Endpoints
# =============================================================================
# What this file does:
#   All /users endpoints: list, create, get by ID, full replace (PUT), partial
#   update (PATCH), and delete. Password changes on PUT/PATCH trigger a Kafka
#   event so the email service can notify the user.
#
# Key decisions:
#   - PUT replaces all fields, PATCH only updates provided fields — this follows
#     REST semantics where PUT = full replacement, PATCH = partial update.
#   - Email is immutable in PATCH to prevent accidental account changes.
#   - password_changed flag: tracks whether password was touched during an update
#     so we only fire the Kafka notification when it actually changed.
#   - Passwords are hashed via bcrypt on every write (create, PUT, PATCH).
# =============================================================================

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List

from app.database import get_db
from app.models import User
from app.schemas.schemas import UserCreate, UserResponse, UserUpdate, Error
from app.utils import build_user_links
from app.auth import get_password_hash
from app.kafka_producer import publish_notification_event

router = APIRouter(prefix="/users", tags=["users"])


@router.get("", response_model=List[UserResponse])
def get_all_users(db: Session = Depends(get_db)):
    users = db.query(User).all()
    for user in users:
        user._links = build_user_links(user.id)
    return users


@router.post("", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
def create_user(user: UserCreate, db: Session = Depends(get_db)):
    existing_user = db.query(User).filter(User.email == user.email).first()
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already registered"
        )

    db_user = User(
        name=user.name,
        email=user.email,
        password=get_password_hash(user.password),
        street_address=user.street_address
    )
    db.add(db_user)
    db.commit()
    db.refresh(db_user)

    db_user._links = build_user_links(db_user.id)
    return db_user


@router.get("/{user_id}", response_model=UserResponse)
def get_user(user_id: int, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")
    user._links = build_user_links(user.id)
    return user


@router.put("/{user_id}", response_model=UserResponse)
def replace_user(user_id: int, user: UserCreate, db: Session = Depends(get_db)):
    db_user = db.query(User).filter(User.id == user_id).first()
    if not db_user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")

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
    db_user.password = get_password_hash(user.password)
    db_user.street_address = user.street_address
    db.commit()
    db.refresh(db_user)

    publish_notification_event(
        event_type='password_changed',
        data={
            'user_id': db_user.id,
            'user_email': db_user.email,
            'user_name': db_user.name
        }
    )

    db_user._links = build_user_links(db_user.id)
    return db_user


@router.patch("/{user_id}", response_model=UserResponse)
def update_user(user_id: int, user: UserUpdate, db: Session = Depends(get_db)):
    """Partial update — email is immutable, only name/address/password can change."""
    db_user = db.query(User).filter(User.id == user_id).first()
    if not db_user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")

    password_changed = False

    if user.name is not None:
        db_user.name = user.name
    if user.street_address is not None:
        db_user.street_address = user.street_address
    if user.password is not None:
        db_user.password = get_password_hash(user.password)
        password_changed = True

    db.commit()
    db.refresh(db_user)

    if password_changed:
        publish_notification_event(
            event_type='password_changed',
            data={
                'user_id': db_user.id,
                'user_email': db_user.email,
                'user_name': db_user.name
            }
        )

    db_user._links = build_user_links(db_user.id)
    return db_user


@router.delete("/{user_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_user(user_id: int, db: Session = Depends(get_db)):
    db_user = db.query(User).filter(User.id == user_id).first()
    if not db_user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")
    db.delete(db_user)
    db.commit()
    return None
