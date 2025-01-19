from typing import List

from domain.entity.PlayerAction import PlayerAction
from domain.repository.base_repository import BaseRepository
from sqlalchemy import or_

class PlayerActionRepository(BaseRepository):
    def find_actions_by_game(self, game_id) -> List[PlayerAction]:
        return self.session.query(PlayerAction)
            .filter(
                PlayerAction.game_id == game_id,
                or_(PlayerAction.action == "buyin", PlayerAction.action == "quit")
            )
            .all()
