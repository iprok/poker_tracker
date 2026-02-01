from dataclasses import dataclass
from typing import Optional


@dataclass
class PlayerData:
    telegram_id: int
    username: Optional[str]
    name: Optional[str]

    @classmethod
    def from_telegram_user(cls, user) -> "PlayerData":
        """Factory method to create PlayerData from telegram.User object."""
        return cls(telegram_id=user.id, username=user.username, name=user.full_name)
