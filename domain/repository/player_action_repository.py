from typing import List

from domain.entity.player_action import PlayerAction
from domain.repository.base_repository import BaseRepository
from sqlalchemy import or_, func


class PlayerActionRepository(BaseRepository):
    def __init__(self, db):
        super().__init__(db)
        self.model = PlayerAction

    def find_actions_by_game(self, game_id) -> List[PlayerAction]:
        return (
            self.db.query(PlayerAction)
            .filter(
                PlayerAction.game_id == game_id,
                or_(PlayerAction.action == "buyin", PlayerAction.action == "quit"),
            )
            .all()
        )

    def user_has_actions_in_game(self, user_id: int, game_id: int) -> bool:
        return (
            self.db.query(self.model)
            .filter_by(user_id=user_id, game_id=game_id)
            .limit(1)
            .first()
            is not None
        )

    def count_distinct_games_by_user(self, user_id: int) -> int:
        return (
            self.db.query(func.count(func.distinct(self.model.game_id)))
            .filter_by(user_id=user_id)
            .scalar()
            or 0
        )

    def get_total_buyin_amount(self, user_id: int) -> int:
        return (
            self.db.query(func.coalesce(func.sum(self.model.amount), 0))
            .filter_by(user_id=user_id, action="buyin")
            .scalar()
            or 0
        )

    def get_total_quit_amount(self, user_id: int) -> int:
        return (
            self.db.query(func.coalesce(func.sum(self.model.amount), 0))
            .filter_by(user_id=user_id, action="quit")
            .scalar()
            or 0
        )

    def get_buyin_count(self, user_id: int) -> int:
        return (
            self.db.query(func.count(self.model.id))
            .filter_by(user_id=user_id, action="buyin")
            .scalar()
            or 0
        )
