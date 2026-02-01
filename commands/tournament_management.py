"""Tournament management commands for the Telegram bot."""

from datetime import datetime, timezone
from telegram import Update
from telegram.ext import ContextTypes


from domain.use_cases.Tournament.start_tournament_use_case import StartTournamentUseCase
from domain.use_cases.Tournament.end_tournament_use_case import EndTournamentUseCase
from domain.use_cases.Tournament.register_player_use_case import RegisterPlayerUseCase
from domain.use_cases.Tournament.eliminate_player_use_case import EliminatePlayerUseCase
from domain.service.notification_public_channel_service import (
    NotificationPublicChannelService,
)
from domain.service.notification_bot_channel_service import (
    NotificationBotChannelService,
)
from domain.scheme.player_data import PlayerData
from utils import get_user_info


class TournamentManagement:
    def __init__(
        self,
        start_tournament_use_case: StartTournamentUseCase,
        end_tournament_use_case: EndTournamentUseCase,
        register_player_use_case: RegisterPlayerUseCase,
        eliminate_player_use_case: EliminatePlayerUseCase,
        notification_public_tournament_channel_service: NotificationPublicChannelService,
        notification_bot_channel_service: NotificationBotChannelService,
    ) -> None:
        self._start_tournament_use_case = start_tournament_use_case
        self._end_tournament_use_case = end_tournament_use_case
        self._register_player_use_case = register_player_use_case
        self._eliminate_player_use_case = eliminate_player_use_case
        self._notification_public_tournament_channel_service = (
            notification_public_tournament_channel_service
        )
        self._notification_bot_channel_service = notification_bot_channel_service

    async def start_tournament(
        self, update: Update, context: ContextTypes.DEFAULT_TYPE
    ) -> None:
        try:
            if not update.effective_user:
                return

            player_data = PlayerData.from_telegram_user(update.effective_user)

            tournament = await self._start_tournament_use_case.execute(player_data)
            await self._notification_public_tournament_channel_service.notify(
                context.bot,
                f"🏆 Турнир #{tournament.id} начат!\n"
                f"Для входа в турнир используйте команду /join_tournament",
            )
        except RuntimeError as e:
            await self._notification_bot_channel_service.reply(
                update, f"❌ Ошибка: {str(e)}"
            )
        except Exception as e:
            await self._notification_bot_channel_service.reply(
                update, f"❌ Произошла непредвиденная ошибка: {str(e)}"
            )

    async def end_tournament(
        self, update: Update, context: ContextTypes.DEFAULT_TYPE
    ) -> None:
        try:
            if not update.effective_user:
                return

            player_data = PlayerData.from_telegram_user(update.effective_user)

            tournament = await self._end_tournament_use_case.execute(player_data)

            await self._notification_public_tournament_channel_service.notify(
                context.bot,
                f"🛑 Турнир завершен.\n"
                f"⏱️ Длительность: {tournament.get_duration_str()}",
            )
        except RuntimeError as e:
            await self._notification_bot_channel_service.reply(
                update, f"❌ Ошибка: {str(e)}"
            )
        except Exception as e:
            await self._notification_bot_channel_service.reply(
                update, f"❌ Произошла непредвиденная ошибка: {str(e)}"
            )

    async def register_player(
        self, update: Update, context: ContextTypes.DEFAULT_TYPE
    ) -> None:
        try:
            if not update.effective_user:
                return

            player_data = PlayerData.from_telegram_user(update.effective_user)

            action = await self._register_player_use_case.execute(player_data)
            await self._notification_public_tournament_channel_service.notify(
                context.bot,
                f"✅ Игрок <b>{action.get_player().get_name()}</b> (@{action.get_player().get_user_name()}) зарегистрирован в турнире!",
            )
        except RuntimeError as e:
            await self._notification_bot_channel_service.reply(
                update, f"❌ Ошибка: {str(e)}"
            )
        except Exception as e:
            await self._notification_bot_channel_service.reply(
                update, f"❌ Произошла непредвиденная ошибка: {str(e)}"
            )

    async def eliminate_player(
        self, update: Update, context: ContextTypes.DEFAULT_TYPE
    ) -> None:
        try:
            if not update.effective_user:
                return

            player_data = PlayerData.from_telegram_user(update.effective_user)

            action = await self._eliminate_player_use_case.execute(player_data)

            await self._notification_public_tournament_channel_service.notify(
                context.bot,
                f"☠️ Игрок <b>{action.get_player().get_name()}</b> (@{action.get_player().get_user_name()}) выбыл из турнира.\n"
                f"🏅 Место: {action.rank}\n"
                f"⏱️ Время в игре: {action.get_duration_str()}",
            )
        except RuntimeError as e:
            await self._notification_bot_channel_service.reply(
                update, f"❌ Ошибка: {str(e)}"
            )
        except Exception as e:
            await self._notification_bot_channel_service.reply(
                update, f"❌ Произошла непредвиденная ошибка: {str(e)}"
            )
