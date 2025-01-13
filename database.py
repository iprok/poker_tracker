from sqlalchemy import create_engine, Column, Integer, String, Float, Boolean, ForeignKey, DateTime
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from datetime import datetime

Base = declarative_base()
engine = create_engine("sqlite:///poker_bot.db")
Session = sessionmaker(bind=engine)
session = Session()

class Game(Base):
    __tablename__ = 'games'
    id = Column(Integer, primary_key=True)
    start_time = Column(DateTime, default=datetime.utcnow)
    end_time = Column(DateTime, nullable=True)

class PlayerAction(Base):
    __tablename__ = 'player_actions'
    id = Column(Integer, primary_key=True)
    game_id = Column(Integer, ForeignKey('games.id'), nullable=False)
    user_id = Column(Integer, nullable=False)
    username = Column(String, nullable=True)
    action = Column(String, nullable=False)
    chips = Column(Integer, nullable=True)
    amount = Column(Float, nullable=True)
    timestamp = Column(DateTime, default=datetime.utcnow)

Base.metadata.create_all(engine)
