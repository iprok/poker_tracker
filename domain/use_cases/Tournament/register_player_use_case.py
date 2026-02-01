from domain.entity.player_tournament_action import TournamentActionType
from domain.scheme.player_data import PlayerData
from domain.repository.player_repository import PlayerRepository
from domain.repository.player_tournament_action_repository import (
    PlayerTournamentActionRepository,
)
from domain.repository.tournament_repository import TournamentRepository
from domain.entity.player_tournament_action import PlayerTournamentAction


class RegisterPlayerUseCase:
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
            raise RuntimeError("Нет активного турнира. Нельзя зарегистрироваться.")

        player = self._player_repository.get_or_create(player_data)

        if self._player_tournament_action_repository.has_player_joined(
            active_tournament.id, player.id
        ):
            raise RuntimeError("Вы уже участвуете в этом турнире.")

        if self._player_tournament_action_repository.is_player_eliminated(
            active_tournament.id, player.id
        ):
            raise RuntimeError("Вы выбыли из турнира и не можете вернуться.")

        action = self._player_tournament_action_repository.add_action(
            active_tournament.id, player.id, TournamentActionType.JOIN
        )

        return action
