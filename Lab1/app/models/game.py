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
