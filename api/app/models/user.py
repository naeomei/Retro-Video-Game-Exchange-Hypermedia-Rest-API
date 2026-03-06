# =============================================================================
# models/user.py — User Database Model
# =============================================================================
# What this file does:
#   Defines the SQLAlchemy ORM model for a user. SQLAlchemy maps this class
#   to a "users" table — each Column() call becomes a column in that table.
#
# Key decisions:
#   - index=True on email: auth queries look up users by email on every request,
#     so indexing it avoids a full table scan on every login.
#   - unique=True on email: enforced at the database level, not just application
#     code, so concurrent requests can't race and create duplicate accounts.
# =============================================================================

from sqlalchemy import Column, Integer, String
from app.database import Base


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False)
    email = Column(String, unique=True, nullable=False, index=True)
    password = Column(String, nullable=False)
    street_address = Column(String, nullable=False)
