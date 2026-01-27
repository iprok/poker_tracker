from fastapi import APIRouter, HTTPException
from engine import Session
from domain.service.player_statistics_service import PlayerStatisticsService
from api.model.player_stats_schema import PlayerActionListResponse, PlayerActionResponse
from cachetools import TTLCache
from config import STATS_BLOCKED_USER_IDS

actions_cache = TTLCache(maxsize=500, ttl=600)  # 10 минут

router = APIRouter()


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
        raise HTTPException(status_code=404, detail="No actions found for this user.")

    response = PlayerActionListResponse(
        actions=[PlayerActionResponse.from_domain(a) for a in actions]
    )
    actions_cache[user_id] = response
    return response
