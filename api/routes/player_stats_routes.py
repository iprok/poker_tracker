from fastapi import APIRouter, HTTPException
from engine import Session
from domain.service.player_statistics_service import PlayerStatisticsService
from domain.model.player_statistics import PlayerStatistics
from api.model.player_stats_schema import PlayerStatsResponse
from cachetools import TTLCache

stats_cache = TTLCache(maxsize=500, ttl=600)  # 10 минут

router = APIRouter()


@router.get(
    "/api/stats/{user_id}",
    response_model=PlayerStatsResponse,
    summary="Get player statistics",
    tags=["Statistics"],
)
def get_player_stats(user_id: int):
    if user_id in stats_cache:
        return stats_cache[user_id]

    session = Session()
    stats_service = PlayerStatisticsService(session)
    stats: PlayerStatistics = stats_service.get_statistics_for_user(user_id)
    session.close()

    if stats.games_num == 0:
        raise HTTPException(
            status_code=404, detail="No statistics found for this user."
        )

    response = PlayerStatsResponse.from_domain(stats)
    stats_cache[user_id] = response
    return response
