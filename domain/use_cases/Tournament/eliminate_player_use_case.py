from datetime import datetime, timezone
from domain.scheme.player_data import PlayerData
from domain.entity.player_tournament_action import (
    TournamentActionType,
    PlayerTournamentAction,
)
from domain.repository.player_repository import PlayerRepository
from domain.repository.player_tournament_action_repository import (
    PlayerTournamentActionRepository,
)
from domain.repository.tournament_repository import TournamentRepository


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

    async def execute(self, player_data: PlayerData) -> PlayerTournamentAction:
        active_tournament = self._tournament_repository.find_active_tournament()
        if not active_tournament:
            raise RuntimeError("Нет активного турнира. Нельзя выбыть.")

        player = self._player_repository.get_or_create(player_data)

        # Retrieve JOIN action to calculate duration
        join_action = self._player_tournament_action_repository.find_action(
            active_tournament.id, player.id, TournamentActionType.JOIN
        )

        if not join_action:
            raise RuntimeError("Вы не участвуете в этом турнире.")

        if self._player_tournament_action_repository.is_player_eliminated(
            active_tournament.id, player.id
        ):
            raise RuntimeError("Вы уже выбыли из этого турнира.")

        # Calculate Rank
        total_players = self._player_tournament_action_repository.count_actions(
            active_tournament.id, TournamentActionType.JOIN
        )
        eliminated_count = self._player_tournament_action_repository.count_actions(
            active_tournament.id, TournamentActionType.ELIMINATE
        )
        rank = total_players - eliminated_count

        # Calculate Duration
        now = datetime.now(timezone.utc)
        created_at = join_action.created_at
        if created_at.tzinfo is None:
            created_at = created_at.replace(tzinfo=timezone.utc)

        duration_seconds = int((now - created_at).total_seconds())

        action = self._player_tournament_action_repository.add_action(
            tournament_id=active_tournament.id,
            player_id=player.id,
            action_type=TournamentActionType.ELIMINATE,
            rank=rank,
            duration_seconds=duration_seconds,
        )
        return action
