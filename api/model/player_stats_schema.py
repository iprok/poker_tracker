from __future__ import annotations
import datetime
from typing import List, Optional
from pydantic import BaseModel
from domain.model.player_statistics import PlayerStatistics
from domain.entity.player_action import PlayerAction


class PlayerStatsResponse(BaseModel):
    games_played: int
    total_buyin: float
    avg_buyins_per_game: float
    profit: float
    roi: float

    @classmethod
    def from_domain(cls, stats: PlayerStatistics) -> PlayerStatsResponse:
        return cls(
            games_played=stats.games_num,
            total_buyin=stats.total_buyin_money,
            avg_buyins_per_game=stats.average_buyin_number,
            profit=stats.profit_money,
            roi=stats.roi,
        )


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
