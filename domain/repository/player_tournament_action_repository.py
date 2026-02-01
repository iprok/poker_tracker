from sqlalchemy import select, and_, func
from datetime import datetime

from domain.entity.player_tournament_action import (
    PlayerTournamentAction,
)
from domain.repository.base_repository import BaseRepository
from typing import Optional, List


class PlayerTournamentActionRepository(BaseRepository):
    def register_player(
        self, tournament_id: int, player_id: int
    ) -> PlayerTournamentAction:
        action = PlayerTournamentAction(
            tournament_id=tournament_id,
            player_id=player_id,
        )
        self.save(action)
        return action

    def eliminate_player(
        self,
        tournament_id: int,
        player_id: int,
        rank: int,
        duration_seconds: int,
        ended_at: datetime,
    ) -> PlayerTournamentAction:
        action = self.find_action(tournament_id, player_id)
        if action:
            action.rank = rank
            action.duration_seconds = duration_seconds
            action.ended_at = ended_at
            self.save(action)
        return action

    def find_action(
        self, tournament_id: int, player_id: int
    ) -> Optional[PlayerTournamentAction]:
        query = select(PlayerTournamentAction).where(
            and_(
                PlayerTournamentAction.tournament_id == tournament_id,
                PlayerTournamentAction.player_id == player_id,
            )
        )
        return self.db.scalar(query)

    def count_total_players(self, tournament_id: int) -> int:
        query = select(func.count(PlayerTournamentAction.id)).where(
            PlayerTournamentAction.tournament_id == tournament_id
        )
        return self.db.scalar(query) or 0

    def count_eliminated_players(self, tournament_id: int) -> int:
        query = select(func.count(PlayerTournamentAction.id)).where(
            and_(
                PlayerTournamentAction.tournament_id == tournament_id,
                PlayerTournamentAction.rank.is_not(None),
            )
        )
        return self.db.scalar(query) or 0

    def has_player_joined(self, tournament_id: int, player_id: int) -> bool:
        return self.find_action(tournament_id, player_id) is not None

    def is_player_eliminated(self, tournament_id: int, player_id: int) -> bool:
        action = self.find_action(tournament_id, player_id)
        return action is not None and action.rank is not None

    def get_active_players(self, tournament_id: int) -> List[str]:
        from domain.entity.player import Player

        # Get players who are in the tournament but have no rank (not eliminated)
        query = (
            select(Player)
            .join(PlayerTournamentAction)
            .where(
                and_(
                    PlayerTournamentAction.tournament_id == tournament_id,
                    PlayerTournamentAction.rank.is_(None),
                )
            )
        )

        players = self.db.scalars(query).all()
        return [f"<b>{p.get_name()}</b> (@{p.get_user_name()})" for p in players]

    def find_actions_by_tournament_id(
        self, tournament_id: int
    ) -> List[PlayerTournamentAction]:
        query = (
            select(PlayerTournamentAction)
            .where(PlayerTournamentAction.tournament_id == tournament_id)
            .order_by(PlayerTournamentAction.created_at.asc())
        )
        return list(self.db.scalars(query).all())
