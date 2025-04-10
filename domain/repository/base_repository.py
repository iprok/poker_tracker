from sqlalchemy.orm import Session
from abc import ABC


class BaseRepository(ABC):
    db: Session

    def __init__(self, db: Session):
        self.db = db

    def save(self, model):
        self.db.add(model)
        self.db.commit()
