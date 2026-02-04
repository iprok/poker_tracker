from sqlalchemy.orm import Session

from config import CHANNEL_ID, CHANNEL_TOURNAMENT_ID
from domain.repository.player_repository import PlayerRepository
from domain.repository.tournament_repository import TournamentRepository
from domain.repository.player_tournament_action_repository import (
    PlayerTournamentActionRepository,
)
from domain.service.notification_public_channel_service import (
    NotificationPublicChannelService,
)
from domain.service.notification_bot_channel_service import (
    NotificationBotChannelService,
)
from domain.use_cases.Tournament.start_tournament_use_case import StartTournamentUseCase
from domain.use_cases.Tournament.end_tournament_use_case import EndTournamentUseCase
from domain.use_cases.Tournament.register_player_use_case import RegisterPlayerUseCase
from domain.use_cases.Tournament.eliminate_player_use_case import EliminatePlayerUseCase
from domain.use_cases.Tournament.get_tournament_summary_use_case import (
    GetTournamentSummaryUseCase,
)
from domain.use_cases.Tournament.shuffle_players_use_case import ShufflePlayersUseCase
from domain.use_cases.Tournament.kick_player_use_case import KickPlayerUseCase


class DIContainer:

    def __init__(self, db_session: Session) -> None:
        self._db_session = db_session
        self._instances: dict = {}

    def get_tournament_repository(self) -> TournamentRepository:
        if "tournament_repository" not in self._instances:
            self._instances["tournament_repository"] = TournamentRepository(
                self._db_session
            )
        return self._instances["tournament_repository"]

    def get_player_repository(self) -> PlayerRepository:
        if "player_repository" not in self._instances:
            self._instances["player_repository"] = PlayerRepository(self._db_session)
        return self._instances["player_repository"]

    def get_start_tournament_use_case(self) -> StartTournamentUseCase:
        if "start_tournament_use_case" not in self._instances:
            self._instances["start_tournament_use_case"] = StartTournamentUseCase(
                tournament_repository=self.get_tournament_repository(),
                player_repository=self.get_player_repository(),
            )
        return self._instances["start_tournament_use_case"]

    def get_end_tournament_use_case(self) -> EndTournamentUseCase:
        if "end_tournament_use_case" not in self._instances:
            self._instances["end_tournament_use_case"] = EndTournamentUseCase(
                tournament_repository=self.get_tournament_repository(),
                player_repository=self.get_player_repository(),
                player_tournament_action_repository=self.get_player_tournament_action_repository(),
            )
        return self._instances["end_tournament_use_case"]

    def get_player_tournament_action_repository(
        self,
    ) -> PlayerTournamentActionRepository:
        if "player_tournament_action_repository" not in self._instances:
            self._instances["player_tournament_action_repository"] = (
                PlayerTournamentActionRepository(self._db_session)
            )
        return self._instances["player_tournament_action_repository"]

    def get_register_player_use_case(self) -> RegisterPlayerUseCase:
        if "register_player_use_case" not in self._instances:
            self._instances["register_player_use_case"] = RegisterPlayerUseCase(
                tournament_repository=self.get_tournament_repository(),
                player_repository=self.get_player_repository(),
                player_tournament_action_repository=self.get_player_tournament_action_repository(),
            )
        return self._instances["register_player_use_case"]

    def get_eliminate_player_use_case(self) -> EliminatePlayerUseCase:
        if "eliminate_player_use_case" not in self._instances:
            self._instances["eliminate_player_use_case"] = EliminatePlayerUseCase(
                tournament_repository=self.get_tournament_repository(),
                player_repository=self.get_player_repository(),
                player_tournament_action_repository=self.get_player_tournament_action_repository(),
            )
        return self._instances["eliminate_player_use_case"]

    def get_notification_public_tournament_channel_service(
        self,
    ) -> NotificationPublicChannelService:
        if "notification_public_tournament_channel_service" not in self._instances:
            self._instances["notification_public_tournament_channel_service"] = (
                NotificationPublicChannelService(CHANNEL_TOURNAMENT_ID)
            )
        return self._instances["notification_public_tournament_channel_service"]

    def get_notification_bot_channel_service(self) -> NotificationBotChannelService:
        if "notification_bot_channel_service" not in self._instances:
            self._instances["notification_bot_channel_service"] = (
                NotificationBotChannelService()
            )
        return self._instances["notification_bot_channel_service"]

    def get_tournament_summary_use_case(self) -> GetTournamentSummaryUseCase:
        if "get_tournament_summary_use_case" not in self._instances:
            self._instances["get_tournament_summary_use_case"] = (
                GetTournamentSummaryUseCase(
                    tournament_repository=self.get_tournament_repository(),
                    player_tournament_action_repository=self.get_player_tournament_action_repository(),
                )
            )
        return self._instances["get_tournament_summary_use_case"]

    def get_shuffle_players_use_case(self) -> ShufflePlayersUseCase:
        if "shuffle_players_use_case" not in self._instances:
            self._instances["shuffle_players_use_case"] = ShufflePlayersUseCase(
                tournament_repository=self.get_tournament_repository(),
                player_tournament_action_repository=self.get_player_tournament_action_repository(),
            )
        return self._instances["shuffle_players_use_case"]

    def get_kick_player_use_case(self) -> KickPlayerUseCase:
        if "kick_player_use_case" not in self._instances:
            self._instances["kick_player_use_case"] = KickPlayerUseCase(
                eliminate_player_use_case=self.get_eliminate_player_use_case(),
                player_repository=self.get_player_repository(),
            )
        return self._instances["kick_player_use_case"]
