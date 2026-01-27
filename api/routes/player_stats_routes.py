from fastapi import APIRouter, HTTPException
from typing import List, Dict
from engine import Session
from domain.service.player_statistics_service import PlayerStatisticsService
from domain.model.player_statistics import PlayerStatistics
from domain.model.player_statistics import PlayerStatistics
from api.model.player_stats_schema import PlayerStatsResponse, PlayerActionListResponse, PlayerActionResponse
from cachetools import TTLCache
from config import STATS_BLOCKED_USER_IDS

stats_cache = TTLCache(maxsize=500, ttl=600)  # 10 минут
roi_cache = TTLCache(maxsize=500, ttl=600)  # 10 минут
actions_cache = TTLCache(maxsize=500, ttl=600)  # 10 минут

router = APIRouter()


@router.get(
    "/api/stats/{user_id}",
    response_model=PlayerStatsResponse,
    summary="Get player statistics",
    tags=["Statistics"],
)
def get_player_stats(user_id: int):
    if user_id in STATS_BLOCKED_USER_IDS:
        raise HTTPException(
            status_code=403, detail="Access denied to stats for this user."
        )

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


@router.get(
    "/api/stats/{user_id}/roi",
    summary="Get player ROI history",
    tags=["Statistics"],
)
def get_player_roi_history(user_id: int) -> List[Dict]:
    if user_id in STATS_BLOCKED_USER_IDS:
        raise HTTPException(
            status_code=403, detail="Access denied to stats for this user."
        )

    if user_id in roi_cache:
        return roi_cache[user_id]

    session = Session()
    stats_service = PlayerStatisticsService(session)
    roi_history = stats_service.get_daily_roi_history(user_id)
    session.close()

    if not roi_history:
        raise HTTPException(
            status_code=404, detail="No ROI history found for this user."
        )

    roi_cache[user_id] = roi_history
    return roi_history


@router.get(
    "/api/stats/{user_id}/actions",
    response_model=PlayerActionListResponse,
    summary="Get player actions history",
    tags=["Statistics"],
)
def get_player_actions(user_id: int):
    if user_id in STATS_BLOCKED_USER_IDS:
        raise HTTPException(
            status_code=403, detail="Access denied to actions for this user."
        )

    if user_id in actions_cache:
        return actions_cache[user_id]

    session = Session()
    stats_service = PlayerStatisticsService(session)
    actions = stats_service.action_repo.get_all_user_actions(user_id)
    session.close()

    if not actions:
        raise HTTPException(
            status_code=404, detail="No actions found for this user."
        )

    response = PlayerActionListResponse(
        actions=[PlayerActionResponse.from_domain(a) for a in actions]
    )
    actions_cache[user_id] = response
    return response
