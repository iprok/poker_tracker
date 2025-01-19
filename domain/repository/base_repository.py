from engine import Session


class BaseRepository:
    db: Session = NotImplementedError

    def __init__(self, db: Session):
        self.db = db

    def save(self, model):
        self.db.add(model)
        self.db.commit()
