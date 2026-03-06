# =============================================================================
# auth.py — HTTP Basic Authentication
# =============================================================================
# What this file does:
#   Provides the authentication layer used by protected endpoints. Reads email
#   and password from the Authorization header (HTTP Basic Auth), looks up the
#   user, and verifies the password against the stored bcrypt hash.
#
# Key decisions:
#   - HTTP Basic Auth: simple and stateless — no sessions or JWT tokens to
#     manage. The client sends credentials on every request in the header.
#   - bcrypt via passlib: bcrypt is intentionally slow, which makes brute-force
#     attacks expensive. passlib wraps it with a consistent API and handles
#     salt generation automatically.
#   - get_current_authenticated_user as a FastAPI Depends: any route that needs
#     auth just declares it as a parameter. FastAPI calls it automatically and
#     injects the resulting User object into the route function.
#   - Same error message for "user not found" and "wrong password": avoids
#     leaking whether an email address exists in the system.
# =============================================================================

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBasic, HTTPBasicCredentials
from sqlalchemy.orm import Session
from passlib.context import CryptContext
from typing import Optional

from app.database import get_db
from app.models.user import User

http_basic_security = HTTPBasic()

# "deprecated=auto" means if we ever switch hashing algorithms, old hashes get
# flagged for re-hashing on the user's next successful login automatically.
password_hashing_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def verify_password(plain_password: str, hashed_password: str) -> bool:
    return password_hashing_context.verify(plain_password, hashed_password)


def get_password_hash(password: str) -> str:
    return password_hashing_context.hash(password)


def get_current_authenticated_user(
    credentials: HTTPBasicCredentials = Depends(http_basic_security),
    database_session: Session = Depends(get_db)
) -> User:
    user_email = credentials.username
    user_password = credentials.password

    authenticated_user = database_session.query(User).filter(User.email == user_email).first()

    if not authenticated_user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password",
            headers={"WWW-Authenticate": "Basic"},
        )

    if not verify_password(user_password, authenticated_user.password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password",
            headers={"WWW-Authenticate": "Basic"},
        )

    return authenticated_user
