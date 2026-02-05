from domain.scheme.player_data import PlayerData
from domain.use_cases.Tournament.eliminate_player_use_case import EliminatePlayerUseCase
from domain.entity.player_tournament_action import PlayerTournamentAction
from typing import Tuple, Optional
from domain.entity.player import Player
from domain.repository.player_repository import PlayerRepository


class KickPlayerUseCase:
    def __init__(
        self,
        eliminate_player_use_case: EliminatePlayerUseCase,
        player_repository: PlayerRepository,
    ):
        self._eliminate_player_use_case = eliminate_player_use_case
        self._player_repository = player_repository

    async def execute(
        self, telegram_id: int
    ) -> Tuple[Player, Optional[PlayerTournamentAction]]:
        player = self._player_repository.find_by_telegram_id(telegram_id)
        if not player:
            raise RuntimeError("Игрок не найден.")

        """
        Kicks a player from the tournament by their telegram_id.
        """
        player_data = PlayerData(telegram_id=telegram_id, username=None, name=None)

        action = await self._eliminate_player_use_case.execute(player_data)

        return player, action
