# =============================================================================
# models/game.py — Game Database Model
# =============================================================================
# What this file does:
#   Defines the SQLAlchemy ORM model for a game listing. Each game is owned
#   by a user, linked via a foreign key.
#
# Key decisions:
#   - ForeignKey("users.id"): enforces referential integrity at the DB level —
#     you can't have a game pointing to a user that doesn't exist.
#   - relationship("User", backref="games"): lets you access game.owner to get
#     the User object, and user.games to get all their games — SQLAlchemy
#     lazy-loads both directions automatically on first access.
# =============================================================================

from sqlalchemy import Column, Integer, String, ForeignKey
from sqlalchemy.orm import relationship
from app.database import Base


class Game(Base):
    __tablename__ = "games"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False)
    publisher = Column(String, nullable=False)
    year_published = Column(Integer, nullable=False)
    system = Column(String, nullable=False)
    condition = Column(String, nullable=False)
    previous_owners = Column(Integer, nullable=True)
    owner_id = Column(Integer, ForeignKey("users.id"), nullable=False)

    owner = relationship("User", backref="games")
