from sqlalchemy import select, and_, func

from domain.entity.player_tournament_action import (
    PlayerTournamentAction,
    TournamentActionType,
)
from domain.repository.base_repository import BaseRepository
from typing import Optional, List


class PlayerTournamentActionRepository(BaseRepository):
    def add_action(
        self,
        tournament_id: int,
        player_id: int,
        action_type: TournamentActionType,
        rank: int = None,
        duration_seconds: int = None,
    ) -> PlayerTournamentAction:
        action = PlayerTournamentAction(
            tournament_id=tournament_id,
            player_id=player_id,
            action_type=action_type,
            rank=rank,
            duration_seconds=duration_seconds,
        )
        self.save(action)
        return action

    def find_action(
        self, tournament_id: int, player_id: int, action_type: TournamentActionType
    ) -> Optional[PlayerTournamentAction]:
        query = select(PlayerTournamentAction).where(
            and_(
                PlayerTournamentAction.tournament_id == tournament_id,
                PlayerTournamentAction.player_id == player_id,
                PlayerTournamentAction.action_type == action_type,
            )
        )
        return self.db.scalar(query)

    def count_actions(
        self, tournament_id: int, action_type: TournamentActionType
    ) -> int:
        query = select(func.count(PlayerTournamentAction.id)).where(
            and_(
                PlayerTournamentAction.tournament_id == tournament_id,
                PlayerTournamentAction.action_type == action_type,
            )
        )
        return self.db.scalar(query) or 0

    def get_player_actions(
        self, tournament_id: int, player_id: int
    ) -> List[PlayerTournamentAction]:
        query = select(PlayerTournamentAction).where(
            and_(
                PlayerTournamentAction.tournament_id == tournament_id,
                PlayerTournamentAction.player_id == player_id,
            )
        )
        return list(self.db.scalars(query).all())

    def has_player_joined(self, tournament_id: int, player_id: int) -> bool:
        return (
            self.find_action(tournament_id, player_id, TournamentActionType.JOIN)
            is not None
        )

    def is_player_eliminated(self, tournament_id: int, player_id: int) -> bool:
        return (
            self.find_action(tournament_id, player_id, TournamentActionType.ELIMINATE)
            is not None
        )

    def get_active_players(self, tournament_id: int) -> List[str]:
        from domain.entity.player import Player

        # Subquery for eliminated player IDs in this tournament
        eliminated_subquery = select(PlayerTournamentAction.player_id).where(
            and_(
                PlayerTournamentAction.tournament_id == tournament_id,
                PlayerTournamentAction.action_type == TournamentActionType.ELIMINATE,
            )
        )

        # Get players who joined but are not in the eliminated IDs
        query = (
            select(Player)
            .join(PlayerTournamentAction)
            .where(
                and_(
                    PlayerTournamentAction.tournament_id == tournament_id,
                    PlayerTournamentAction.action_type == TournamentActionType.JOIN,
                    Player.id.not_in(eliminated_subquery),
                )
            )
        )

        players = self.db.scalars(query).all()
        return [f"<b>{p.get_name()}</b> (@{p.get_user_name()})" for p in players]
