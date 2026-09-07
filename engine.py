from sqlalchemy import create_engine
from sqlalchemy.orm import declarative_base, sessionmaker

Base = declarative_base()
Engine = create_engine("sqlite:///poker_bot.db")
Session = sessionmaker(bind=Engine)
session = Session()
