import random
from typing import List, Dict, Any
from domain.repository.tournament_repository import TournamentRepository
from domain.repository.player_tournament_action_repository import (
    PlayerTournamentActionRepository,
)


class ShufflePlayersUseCase:
    def __init__(
        self,
        tournament_repository: TournamentRepository,
        player_tournament_action_repository: PlayerTournamentActionRepository,
    ) -> None:
        self._tournament_repository = tournament_repository
        self._player_tournament_action_repository = player_tournament_action_repository

    async def execute(self) -> Dict[str, Any]:
        tournament = self._tournament_repository.find_active_tournament()
        if not tournament:
            raise RuntimeError("Нет активного турнира для перемешивания игроков.")

        players = self._player_tournament_action_repository.find_active_player_entities(
            tournament.id
        )

        if not players:
            raise RuntimeError("В турнире пока нет активных игроков.")

        if tournament.is_shuffled:
            raise RuntimeError("Игроки уже были перемешаны для этого турнира.")

        # Shuffle players randomly
        random.shuffle(players)

        tournament.is_shuffled = True
        self._tournament_repository.save(tournament)

        tables = []
        if len(players) > 9:
            # Split into 2 tables
            mid = len(players) // 2
            tables.append(players[:mid])
            tables.append(players[mid:])
        else:
            # Single table
            tables.append(players)

        # Update table and position assignments in repository
        for i, table_players in enumerate(tables, 1):
            for j, player in enumerate(table_players, 1):
                self._player_tournament_action_repository.update_table_and_position_assignment(
                    tournament.id, player.id, i, j
                )

        return {
            "tournament_id": tournament.id,
            "tables": tables,
            "total_players": len(players),
        }
