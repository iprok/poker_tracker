from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

Base = declarative_base()
Engine = create_engine("sqlite:///poker_bot.db")
Session = sessionmaker(bind=Engine)
session = Session()
