from typing import List
from fastapi import APIRouter, HTTPException
from sqlalchemy import select
from domain.entity.tournament import Tournament
from engine import Session
from domain.repository.tournament_repository import TournamentRepository
from domain.scheme.tournament_scheme import (
    TournamentResponse,
    TournamentDetailResponse,
    PlayerTournamentStateResponse,
)
from domain.repository.player_tournament_action_repository import (
    PlayerTournamentActionRepository,
)

router = APIRouter()


@router.get(
    "/api/tournaments",
    response_model=List[TournamentResponse],
    summary="Get all tournaments",
    tags=["Tournaments"],
)
def get_tournaments():
    session = Session()
    try:
        repo = TournamentRepository(session)
        tournaments = repo.get_all_tournaments()

        from domain.repository.player_tournament_action_repository import (
            PlayerTournamentActionRepository,
        )

        action_repo = PlayerTournamentActionRepository(session)

        response = []
        for t in tournaments:
            model = TournamentResponse.from_domain(t)

            # Fetch winners
            # We need a new method in action_repo or just query directly here for simplicity for now
            # But better to use repository method.
            # Let's add a method get_winners(tournament_id) to PlayerTournamentActionRepository.
            winners_actions = action_repo.get_winners(t.id)
            model.winners = [
                f"{w.player.name or w.player.username}" for w in winners_actions
            ]
            model.total_players = action_repo.count_total_players(t.id)
            response.append(model)

        return response
    finally:
        session.close()


@router.get(
    "/api/tournaments/{tournament_id}",
    response_model=TournamentDetailResponse,
    summary="Get tournament details",
    tags=["Tournaments"],
)
def get_tournament_details(tournament_id: int):
    session = Session()
    try:
        repo = TournamentRepository(session)
        tournament = repo.db.scalar(
            select(Tournament).where(Tournament.id == tournament_id)
        )

        if not tournament:
            raise HTTPException(status_code=404, detail="Tournament not found")

        action_repo = PlayerTournamentActionRepository(session)
        actions = action_repo.find_actions_by_tournament_id(tournament_id)

        participants = []
        for action in actions:
            status = "Active"
            if action.rank:
                status = "Eliminated"
            # It's hard to distinguish "Joined" vs "Active" if tournament started.
            # If tournament hasn't started, everyone is "Registered"
            if not tournament.is_shuffled:
                status = "Registered"

            participants.append(
                PlayerTournamentStateResponse(
                    player_id=action.player_id,
                    username=action.player.username,
                    name=action.player.name,
                    rank=action.rank,
                    table_number=action.table_number,
                    position_number=action.position_number,
                    duration_seconds=action.duration_seconds,
                    created_at=action.created_at,
                    ended_at=action.ended_at,
                    status=status,
                )
            )

        # Create base response first
        base_model = TournamentResponse.from_domain(tournament)
        model_dict = base_model.model_dump()

        model_dict["participants"] = participants

        # Also fill winners and total_players
        model_dict["winners"] = [
            f"{p.name or p.username}"
            for p in sorted(
                [p for p in participants if p.rank and p.rank <= 3],
                key=lambda x: x.rank,
            )
        ]
        model_dict["total_players"] = len(participants)

        return TournamentDetailResponse(**model_dict)
    finally:
        session.close()
