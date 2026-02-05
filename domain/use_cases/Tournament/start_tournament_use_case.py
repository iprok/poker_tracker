from datetime import datetime, timezone
from typing import Optional
from domain.scheme.player_data import PlayerData

from domain.entity.tournament import Tournament
from domain.repository.tournament_repository import TournamentRepository


from domain.repository.player_repository import PlayerRepository


class StartTournamentUseCase:
    def __init__(
        self,
        tournament_repository: TournamentRepository,
        player_repository: PlayerRepository,
    ) -> None:
        self._tournament_repository = tournament_repository
        self._player_repository = player_repository

    async def execute(self, player_data: PlayerData) -> Tournament:
        active_tournament = self._tournament_repository.find_active_tournament()
        if active_tournament:
            raise RuntimeError(
                f"Нельзя создать новый турнир. Турнир #{active_tournament.id} уже активен."
            )

        player = self._player_repository.get_or_create(player_data)

        new_tournament = Tournament(
            created_at=datetime.now(timezone.utc),
            start_time=None,
            end_time=None,
            created_player=player,
        )

        self._tournament_repository.save(new_tournament)

        return new_tournament
