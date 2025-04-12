from fastapi import APIRouter, HTTPException
from engine import Session
from domain.service.player_statistics_service import PlayerStatisticsService
from domain.model.player_statistics import PlayerStatistics
from api.model.player_stats_schema import PlayerStatsResponse

router = APIRouter()


@router.get(
    "/api/stats/{user_id}",
    response_model=PlayerStatsResponse,
    summary="Get player statistics",
    tags=["Statistics"],
)
def get_player_stats(user_id: int):
    session = Session()
    stats_service = PlayerStatisticsService(session)
    stats: PlayerStatistics = stats_service.get_statistics_for_user(user_id)
    session.close()

    if stats.games_num == 0:
        raise HTTPException(
            status_code=404, detail="No statistics found for this user."
        )

    return PlayerStatsResponse.from_domain(stats)
