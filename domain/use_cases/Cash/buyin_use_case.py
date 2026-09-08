from dataclasses import dataclass

from domain.repository.game_repository import GameRepository
from domain.repository.player_action_repository import PlayerActionRepository


class NoActiveGameError(Exception):
    """A buy-in requires an unfinished game."""


@dataclass(frozen=True)
class BuyinResult:
    game_id: int
    chips: int
    amount: float
    buyin_count: int
    buyin_total: float


class BuyinUseCase:
    """Record a buy-in inside the caller's transaction, without Telegram I/O."""

    def __init__(
        self,
        games: GameRepository,
        actions: PlayerActionRepository,
        chip_count: int,
        chip_value: float,
    ):
        self.games = games
        self.actions = actions
        self.chip_count = chip_count
        self.chip_value = chip_value

    def execute(self, user_id: int, username: str | None) -> BuyinResult:
        game = self.games.find_active_game()
        if game is None:
            raise NoActiveGameError()
        self.actions.add_buyin(
            game.id, user_id, username, self.chip_count, self.chip_value
        )
        count, total = self.actions.get_game_buyin_totals(game.id, user_id)
        return BuyinResult(game.id, self.chip_count, self.chip_value, count, total)
