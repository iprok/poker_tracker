from datetime import datetime, timezone
from database import Session, Game, PlayerAction
from telegram import Update
from telegram.ext import ContextTypes
from prettytable import PrettyTable
from config import CHIP_VALUE, CHIP_COUNT, CHANNEL_ID, USE_TABLE

class GameManagement:

    @staticmethod
    async def start_game(update: Update, context: ContextTypes.DEFAULT_TYPE):
        session = Session()
        current_game = session.query(Game).filter_by(end_time=None).first()
        if current_game:
            await update.message.reply_text("Игра уже начата!")
            session.close()
            return

        new_game = Game(start_time=datetime.now(timezone.utc))
        session.add(new_game)
        session.commit()

        # Сохраняем game_id в контексте бота
        context.bot_data["current_game_id"] = new_game.id

        session.close()
        await update.message.reply_text("Игра начата! Закупки открыты.")

    @staticmethod
    async def end_game(update: Update, context: ContextTypes.DEFAULT_TYPE):
        session = Session()
        current_game = session.query(Game).filter_by(end_time=None).first()
        if not current_game:
            await update.message.reply_text("Игра не начата.")
            session.close()
            return

        current_game.end_time = datetime.now(timezone.utc)
        session.commit()

        # Удаляем текущий game_id из контекста
        context.bot_data.pop("current_game_id", None)

        session.close()
        await update.message.reply_text("Игра завершена.")

    @staticmethod
    async def summary(update: Update, context: ContextTypes.DEFAULT_TYPE):
        session = Session()
        current_game_id = context.bot_data.get("current_game_id")
        if current_game_id is None:
            await update.message.reply_text("Игра не начата.")
            session.close()
            return

        actions = session.query(PlayerAction).filter_by(game_id=current_game_id).all()
        if not actions:
            await update.message.reply_text("Закупов в текущей игре ещё не было.")
            session.close()
            return

        if USE_TABLE:
            table = PrettyTable()
            table.field_names = ["Имя", "buy", "quit", "diff"]

            player_stats = {}
            for action in actions:
                if action.username not in player_stats:
                    player_stats[action.username] = {"buyin": 0, "quit": 0}

                if action.action == "buyin":
                    player_stats[action.username]["buyin"] += action.amount
                elif action.action == "quit":
                    player_stats[action.username]["quit"] += action.amount

            for username, stats in player_stats.items():
                balance = stats["quit"] - stats["buyin"]
                table.add_row([username, f"{stats['buyin']:.2f}", f"{stats['quit']:.2f}", f"{balance:.2f}"])

            summary_text = f"<pre>Сводка закупов:\n{table}</pre>"
            await update.message.reply_text(summary_text, parse_mode="HTML")
        else:
            summary_text = "Сводка закупов:\n"
            for action in actions:
                summary_text += f"{action.username} - {action.action}: {action.amount} лева\n"
            await update.message.reply_text(summary_text)

        session.close()