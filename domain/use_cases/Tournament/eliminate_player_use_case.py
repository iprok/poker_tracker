from datetime import datetime, timezone
from domain.scheme.player_data import PlayerData
from domain.entity.player_tournament_action import (
    PlayerTournamentAction,
)
from domain.repository.player_repository import PlayerRepository
from domain.repository.player_tournament_action_repository import (
    PlayerTournamentActionRepository,
)
from domain.repository.tournament_repository import TournamentRepository
from typing import Optional


class EliminatePlayerUseCase:
    def __init__(
        self,
        tournament_repository: TournamentRepository,
        player_repository: PlayerRepository,
        player_tournament_action_repository: PlayerTournamentActionRepository,
    ):
        self._tournament_repository = tournament_repository
        self._player_repository = player_repository
        self._player_tournament_action_repository = player_tournament_action_repository

    async def execute(
        self, player_data: PlayerData
    ) -> Optional[PlayerTournamentAction]:
        active_tournament = self._tournament_repository.find_active_tournament()
        if not active_tournament:
            raise RuntimeError("Нет активного турнира. Нельзя выбыть.")

        player = self._player_repository.get_or_create(player_data)

        # Retrieve JOIN record (which is the only record for this player/tournament)
        action = self._player_tournament_action_repository.find_action(
            active_tournament.id, player.id
        )

        if not action:
            raise RuntimeError("Вы не участвуете в этом турнире.")

        if not active_tournament.is_tournament_started():
            self._player_tournament_action_repository.unregister_player(action)

            return None

        if action.rank is not None:
            raise RuntimeError("Вы уже выбыли из этого турнира.")

        # Calculate Rank
        total_players = self._player_tournament_action_repository.count_total_players(
            active_tournament.id
        )
        eliminated_count = (
            self._player_tournament_action_repository.count_eliminated_players(
                active_tournament.id
            )
        )
        rank = total_players - eliminated_count

        # Calculate Duration
        now = datetime.now(timezone.utc)
        start_time = active_tournament.start_time
        if not start_time:
            # Fallback if start_time is missing (should not happen for active tournament)
            start_time = now

        if start_time.tzinfo is None:
            start_time = start_time.replace(tzinfo=timezone.utc)

        duration_seconds = int((now - start_time).total_seconds())

        action = self._player_tournament_action_repository.eliminate_player(
            tournament_id=active_tournament.id,
            player_id=player.id,
            rank=rank,
            duration_seconds=duration_seconds,
            ended_at=now,
        )
        return action
