from typing import List

from domain.entity.game import Game
from domain.repository.base_repository import BaseRepository
from sqlalchemy import desc


class GameRepository(BaseRepository):
    def find_active_game(self) -> Game:
        return self.db.query(Game).filter_by(end_time=None).first()

    def get_games_by_limit(self, limit: int) -> List[Game]:
        return self.db.query(Game).order_by(desc(Game.id)).limit(limit).all()

    # def get_all_games(self) -> List[Game]:
    #     return self.db.query(Game).all()
