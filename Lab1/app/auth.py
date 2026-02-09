from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBasic, HTTPBasicCredentials
from sqlalchemy.orm import Session
from passlib.context import CryptContext
from typing import Optional

from app.database import get_db
from app.models.user import User

http_basic_security = HTTPBasic()

password_hashing_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """
    Verify a plain password against a hashed password using bcrypt.

    Args:
        plain_password: The password provided by the user
        hashed_password: The bcrypt hash stored in the database

    Returns:
        True if passwords match, False otherwise
    """
    return password_hashing_context.verify(plain_password, hashed_password)


def get_password_hash(password: str) -> str:
    """
    Hash a plain password using bcrypt for secure storage.

    Args:
        password: The plain text password to hash

    Returns:
        The bcrypt hashed password
    """
    return password_hashing_context.hash(password)


def get_current_authenticated_user(
    credentials: HTTPBasicCredentials = Depends(http_basic_security),
    database_session: Session = Depends(get_db)
) -> User:
    """
    Dependency function that extracts and validates user credentials from HTTP Basic Auth.

    This function is used as a FastAPI dependency to protect endpoints.
    If credentials are invalid, it raises an HTTP 401 exception.

    Args:
        credentials: The HTTP Basic Auth credentials extracted from the request header
        database_session: The database session for querying the user

    Returns:
        The authenticated User object from the database

    Raises:
        HTTPException: 401 Unauthorized if credentials are invalid
    """
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
