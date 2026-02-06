from typing import Optional, List
from datetime import datetime
from pydantic import BaseModel


class TournamentResponse(BaseModel):
    id: int
    created_at: datetime
    start_time: Optional[datetime] = None
    end_time: Optional[datetime] = None
    is_shuffled: bool
    created_player_id: Optional[int] = None
    ended_player_id: Optional[int] = None
    duration: Optional[str] = None
    status: str = "Pending"
    winners: List[str] = []
    total_players: int = 0

    model_config = {"from_attributes": True}

    @classmethod
    def from_domain(cls, obj):

        if isinstance(obj, dict):
            # If obj is a dict (from API call inside route?), handle it.
            # But normally we pass the SQLAlchemy object.
            # Assuming obj is Tournament entity.
            pass

        model = cls.model_validate(obj)
        model.duration = (
            obj.get_duration_str() if obj.start_time and obj.end_time else None
        )

        if obj.is_tournament_ended():
            model.status = "Completed"
        elif obj.is_tournament_started():
            model.status = "Active"
        else:
            model.status = "Pending"

        return model


class PlayerTournamentStateResponse(BaseModel):
    player_id: int
    username: Optional[str] = None
    name: Optional[str] = None
    rank: Optional[int] = None
    table_number: Optional[int] = None
    position_number: Optional[int] = None
    duration_seconds: Optional[int] = None
    created_at: datetime
    ended_at: Optional[datetime] = None
    status: str

    model_config = {"from_attributes": True}


class TournamentDetailResponse(TournamentResponse):
    participants: List[PlayerTournamentStateResponse]
