from sqlalchemy import Column, Integer, String, Float, ForeignKey, DateTime
from datetime import datetime, timezone
from engine import Base, Engine


class PlayerAction(Base):
    __tablename__ = "player_actions"
    id = Column(Integer, primary_key=True)
    game_id = Column(Integer, ForeignKey("games.id"), nullable=False)
    user_id = Column(Integer, nullable=False)
    username = Column(String, nullable=True)
    action = Column(String, nullable=False)
    chips = Column(Integer, nullable=True)
    amount = Column(Float, nullable=True)
    timestamp = Column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc)
    )


Base.metadata.create_all(Engine)
