from typing import List

from domain.entity.tournament import Tournament
from domain.repository.base_repository import BaseRepository


class TournamentRepository(BaseRepository):
    def find_active_tournament(self) -> Tournament:
        return self.db.query(Tournament).filter_by(end_time=None).first()
