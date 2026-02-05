from sqlalchemy.orm import Session
from abc import ABC


class BaseRepository(ABC):
    db: Session

    def __init__(self, db: Session):
        self.db = db
        self.model = None  # позже будет переопределён в потомках

    def save(self, model):
        self.db.add(model)
        self.db.commit()

    def delete(self, model):
        self.db.delete(model)
        self.db.commit()
