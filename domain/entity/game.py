from sqlalchemy import Column, Integer, DateTime
from datetime import datetime
from engine import Base, Engine


class Game(Base):
    __tablename__ = "games"
    id = Column(Integer, primary_key=True)
    start_time = Column(DateTime, default=datetime.utcnow)
    end_time = Column(DateTime, nullable=True)


Base.metadata.create_all(Engine)
