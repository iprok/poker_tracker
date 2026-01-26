from __future__ import annotations

from pydantic import BaseModel
from domain.model.player_statistics import PlayerStatistics


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
