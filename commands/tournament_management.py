"""Tournament management commands for the Telegram bot."""

from datetime import datetime, timezone
from telegram import Update
from telegram.ext import ContextTypes


from domain.use_cases.Tournament.start_tournament_use_case import StartTournamentUseCase
from domain.use_cases.Tournament.end_tournament_use_case import EndTournamentUseCase
from domain.use_cases.Tournament.register_player_use_case import RegisterPlayerUseCase
from domain.use_cases.Tournament.eliminate_player_use_case import EliminatePlayerUseCase
from domain.use_cases.Tournament.get_tournament_summary_use_case import (
    GetTournamentSummaryUseCase,
)
from domain.use_cases.Tournament.shuffle_players_use_case import ShufflePlayersUseCase
from domain.service.notification_public_channel_service import (
    NotificationPublicChannelService,
)
from domain.service.notification_bot_channel_service import (
    NotificationBotChannelService,
)
from domain.scheme.player_data import PlayerData
from utils import get_user_info, setup_bot_commands
from config import CHANNEL_TOURNAMENT_ID


class TournamentManagement:
    def __init__(
        self,
        start_tournament_use_case: StartTournamentUseCase,
        end_tournament_use_case: EndTournamentUseCase,
        register_player_use_case: RegisterPlayerUseCase,
        eliminate_player_use_case: EliminatePlayerUseCase,
        get_tournament_summary_use_case: GetTournamentSummaryUseCase,
        shuffle_players_use_case: ShufflePlayersUseCase,
        notification_public_tournament_channel_service: NotificationPublicChannelService,
        notification_bot_channel_service: NotificationBotChannelService,
    ) -> None:
        self._start_tournament_use_case = start_tournament_use_case
        self._end_tournament_use_case = end_tournament_use_case
        self._register_player_use_case = register_player_use_case
        self._eliminate_player_use_case = eliminate_player_use_case
        self._get_tournament_summary_use_case = get_tournament_summary_use_case
        self._shuffle_players_use_case = shuffle_players_use_case
        self._notification_public_tournament_channel_service = (
            notification_public_tournament_channel_service
        )
        self._notification_bot_channel_service = notification_bot_channel_service

    async def shuffle_players(
        self, update: Update, context: ContextTypes.DEFAULT_TYPE
    ) -> None:
        try:
            result = await self._shuffle_players_use_case.execute()
            tables = result["tables"]

            message = [
                f"🎲 <b>Рассадка игроков (Турнир #{result['tournament_id']})</b>\n"
            ]

            for i, table_players in enumerate(tables, 1):
                message.append(f"<b>Стол №{i}</b>")
                for j, player in enumerate(table_players, 1):
                    message.append(
                        f"🪑 {j}: <b>{player.get_name()}</b> (@{player.get_user_name()})"
                    )
                message.append("")  # Empty line between tables

            await self._notification_public_tournament_channel_service.notify(
                context.bot, "\n".join(message)
            )

            await self._notification_bot_channel_service.reply(
                update, "✅ Игроки перемешаны. Результат отправлен в канал турнира."
            )
        except Exception as e:
            await self._notification_bot_channel_service.reply(
                update, f"❌ Ошибка при перемешивании: {str(e)}"
            )

    async def summary_tournament(
        self, update: Update, context: ContextTypes.DEFAULT_TYPE
    ) -> None:
        try:
            summary = await self._get_tournament_summary_use_case.execute()
            tournament = summary["tournament"]

            if not tournament:
                await self._notification_bot_channel_service.reply(
                    update, "❌ Турниры ещё не проводились."
                )
                return

            status = "Активный" if summary["is_active"] else "Завершенный"
            message = [f"📊 <b>Турнир #{tournament.id}</b> ({status})\n"]

            if not summary["players"]:
                message.append("Игроков пока нет.")
            else:
                for idx, player_info in enumerate(summary["players"], 1):
                    player = player_info["player"]
                    rank = player_info["rank"]
                    duration = player_info.get("duration_str")

                    rank_str = f"🏅 Место: {rank}" if rank else "🎮 В игре"
                    duration_str = f" (⏱ {duration})" if duration else ""
                    message.append(
                        f"{idx}. <b>{player.get_name()}</b> (@{player.get_user_name()}) — {rank_str}{duration_str}"
                    )

            await self._notification_bot_channel_service.reply(
                update, "\n".join(message)
            )
        except Exception as e:
            await self._notification_bot_channel_service.reply(
                update, f"❌ Ошибка при получении сводки: {str(e)}"
            )

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
                f"В личном чате с ботом появились кнопки:\n"
                f"<b>Вступить в турнир</b>\n"
                f"<b>Покинуть турнир</b>\n",
            )
            # Update dynamic commands
            await setup_bot_commands(context.bot)
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
            # Update dynamic commands
            await setup_bot_commands(context.bot)
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
