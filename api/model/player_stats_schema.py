from __future__ import annotations
import datetime
from typing import List, Optional
from pydantic import BaseModel
from domain.entity.player_action import PlayerAction


class PlayerActionResponse(BaseModel):
    game_id: int
    action: int  # 1: buyin, 2: quit
    amount: Optional[float]
    timestamp: int  # Unix timestamp

    @classmethod
    def from_domain(cls, action: PlayerAction) -> PlayerActionResponse:
        action_map = {"buyin": 1, "quit": 2}
        return cls(
            game_id=action.game_id,
            action=action_map.get(action.action, 0),
            amount=action.amount,
            timestamp=int(action.timestamp.timestamp()),
        )


class PlayerActionListResponse(BaseModel):
    actions: List[PlayerActionResponse]
