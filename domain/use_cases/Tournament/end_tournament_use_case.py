from datetime import datetime, timezone
from domain.scheme.player_data import PlayerData
from domain.entity.player_tournament_action import TournamentActionType
from domain.repository.tournament_repository import TournamentRepository
from domain.repository.player_repository import PlayerRepository
from domain.repository.player_tournament_action_repository import (
    PlayerTournamentActionRepository,
)


from domain.entity.tournament import Tournament


class EndTournamentUseCase:
    def __init__(
        self,
        tournament_repository: TournamentRepository,
        player_repository: PlayerRepository,
        player_tournament_action_repository: PlayerTournamentActionRepository,
    ) -> None:
        self._tournament_repository = tournament_repository
        self._player_repository = player_repository
        self._player_tournament_action_repository = player_tournament_action_repository

    async def execute(self, player_data: PlayerData) -> Tournament:
        active_tournament = self._tournament_repository.find_active_tournament()
        if not active_tournament:
            raise RuntimeError("Нельзя завершить турнир. Активный турнир не найден.")

        # Check if all players are eliminated
        total_players = self._player_tournament_action_repository.count_actions(
            active_tournament.id, TournamentActionType.JOIN
        )
        eliminated_count = self._player_tournament_action_repository.count_actions(
            active_tournament.id, TournamentActionType.ELIMINATE
        )

        if total_players > eliminated_count:
            active_players = (
                self._player_tournament_action_repository.get_active_players(
                    active_tournament.id
                )
            )
            raise RuntimeError(
                f"Нельзя завершить турнир. Ещё осталось {len(active_players)} активных игроков.\n\n"
                f"Активные игроки:\n" + "\n".join(active_players)
            )

        player = self._player_repository.get_or_create(player_data)

        active_tournament.end_time = datetime.now(timezone.utc)
        active_tournament.ended_player = player

        self._tournament_repository.save(active_tournament)
        return active_tournament
