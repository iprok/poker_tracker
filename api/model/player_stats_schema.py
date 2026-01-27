from __future__ import annotations
import datetime
from typing import List, Optional
from pydantic import BaseModel
from domain.entity.player_action import PlayerAction


class PlayerActionResponse(BaseModel):
    id: int
    user_id: int
    game_id: int
    action: str
    amount: Optional[float]
    timestamp: datetime.datetime

    @classmethod
    def from_domain(cls, action: PlayerAction) -> PlayerActionResponse:
        return cls(
            id=action.id,
            user_id=action.user_id,
            game_id=action.game_id,
            action=action.action,
            amount=action.amount,
            timestamp=action.timestamp,
        )


class PlayerActionListResponse(BaseModel):
    actions: List[PlayerActionResponse]
