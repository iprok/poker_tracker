from typing import List, Dict, Any, Optional
from domain.repository.tournament_repository import TournamentRepository
from domain.repository.player_tournament_action_repository import (
    PlayerTournamentActionRepository,
)


class GetTournamentSummaryUseCase:
    def __init__(
        self,
        tournament_repository: TournamentRepository,
        player_tournament_action_repository: PlayerTournamentActionRepository,
    ) -> None:
        self._tournament_repository = tournament_repository
        self._player_tournament_action_repository = player_tournament_action_repository

    async def execute(self) -> Dict[str, Any]:
        tournament = self._tournament_repository.find_active_tournament()
        is_active = True

        if not tournament:
            tournament = self._tournament_repository.find_latest_tournament()
            is_active = False

        if not tournament:
            return {"tournament": None, "players": [], "is_active": False}

        actions = (
            self._player_tournament_action_repository.find_actions_by_tournament_id(
                tournament.id
            )
        )

        sorted_players = []
        for action in actions:
            sorted_players.append(
                {
                    "player": action.get_player(),
                    "rank": action.rank,
                    "duration_str": (
                        action.get_duration_str() if action.rank is not None else None
                    ),
                    "joined_at": action.created_at,
                    "eliminated_at": action.ended_at,
                }
            )

        # Sort:
        # User requested: "sort by rank or join date."
        # Here we sort by rank (ELIMINATED last or first? usually rank 1 is last to stay)
        # If rank is None, they are in game.
        sorted_players.sort(
            key=lambda x: (
                x["rank"] if x["rank"] is not None else float("inf"),
                x["joined_at"],
            )
        )

        return {
            "tournament": tournament,
            "players": sorted_players,
            "is_active": is_active,
        }
