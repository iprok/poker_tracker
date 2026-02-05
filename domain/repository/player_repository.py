from typing import Optional, TYPE_CHECKING

if TYPE_CHECKING:
    from domain.scheme.player_data import PlayerData
from sqlalchemy import select
from sqlalchemy.orm import Session

from domain.entity.player import Player
from domain.repository.base_repository import BaseRepository


class PlayerRepository(BaseRepository):
    def find_by_telegram_id(self, telegram_id: int) -> Optional[Player]:
        return self.db.scalar(select(Player).where(Player.telegram_id == telegram_id))

    def get_or_create(self, player_data: "PlayerData") -> Player:
        player = self.find_by_telegram_id(player_data.telegram_id)
        if not player:
            player = Player(
                telegram_id=player_data.telegram_id,
                username=player_data.username,
                name=player_data.name,
            )

        # Update fields if changed and provided
        if player_data.username and player.username != player_data.username:
            player.username = player_data.username
        if player_data.name and player.name != player_data.name:
            player.name = player_data.name

        self.save(player)
        return player
