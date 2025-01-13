#!/usr/bin/env python3

from telegram import Update
from telegram.ext import Application, CommandHandler, ContextTypes
from database import Session, Game, PlayerAction
from config import BOT_TOKEN, CHANNEL_ID, CHIP_VALUE, CHIP_COUNT, TIMEZONE, USE_TABLE
from datetime import datetime, timezone
import pytz
from prettytable import PrettyTable

class PokerBot:
    def __init__(self):
        self.current_game_id = None
        self.application = Application.builder().token(BOT_TOKEN).build()
        self.timezone = pytz.timezone(TIMEZONE)
        self._register_handlers()

    def _register_handlers(self):
        self.application.add_handler(CommandHandler("startgame", self.start_game))
        self.application.add_handler(CommandHandler("buyin", self.buyin))
        self.application.add_handler(CommandHandler("quit", self.quit_game))
        self.application.add_handler(CommandHandler("endgame", self.end_game))
        self.application.add_handler(CommandHandler("summary", self.summary))
        self.application.add_handler(CommandHandler("log", self.log))
        self.application.add_handler(CommandHandler("help", self.help))

    def format_datetime(self, dt):
        return dt.astimezone(self.timezone).strftime("%d-%m-%Y %H:%M:%S")

    async def start_game(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        if self.current_game_id is not None:
            await update.message.reply_text("Игра уже начата!")
            return

        session = Session()
        new_game = Game(start_time=datetime.now(timezone.utc))
        session.add(new_game)
        session.commit()
        self.current_game_id = new_game.id

        # Log the start of the game
        action = PlayerAction(
            game_id=self.current_game_id,
            user_id=update.effective_user.id,
            username=update.effective_user.username,
            action="start_game",
            chips=None,
            amount=None,
            timestamp=datetime.now(timezone.utc)
        )
        session.add(action)
        session.commit()
        session.close()

        await update.message.reply_text("Игра начата! Закупки открыты.")

    async def buyin(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        if self.current_game_id is None:
            await update.message.reply_text("Сначала начните игру командой /startgame.")
            return

        user = update.effective_user
        session = Session()
        action = PlayerAction(
            game_id=self.current_game_id,
            user_id=user.id,
            username=user.username,
            action="buyin",
            chips=CHIP_COUNT,
            amount=CHIP_VALUE
        )
        session.add(action)
        session.commit()
        session.close()
        await update.message.reply_text(f"Закуп на {CHIP_COUNT} фишек ({CHIP_VALUE} лева) записан.")

    async def quit_game(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        if self.current_game_id is None:
            await update.message.reply_text("Сначала начните игру командой /startgame.")
            return

        user = update.effective_user
        try:
            chips_left = int(context.args[0])
        except (IndexError, ValueError):
            await update.message.reply_text("Укажите количество фишек после выхода, например: /quit 1500")
            return

        amount = (chips_left / CHIP_COUNT) * CHIP_VALUE
        session = Session()
        action = PlayerAction(
            game_id=self.current_game_id,
            user_id=user.id,
            username=user.username,
            action="quit",
            chips=chips_left,
            amount=amount
        )
        session.add(action)
        session.commit()
        session.close()
        await update.message.reply_text(f"Выход записан. У вас осталось {chips_left} фишек, что эквивалентно {amount:.2f} лева.")

    async def end_game(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        if self.current_game_id is None:
            await update.message.reply_text("Игра не начата.")
            return

        session = Session()
        game = session.get(Game, self.current_game_id)
        game.end_time = datetime.now(timezone.utc)

        # Log the end of the game
        action = PlayerAction(
            game_id=self.current_game_id,
            user_id=update.effective_user.id,
            username=update.effective_user.username,
            action="end_game",
            chips=None,
            amount=None,
            timestamp=datetime.now(timezone.utc)
        )
        session.add(action)

        # Commit all changes in one transaction
        session.commit()
        session.close()

        self.current_game_id = None
        await update.message.reply_text("Игра завершена.")

    async def summary(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        if self.current_game_id is None:
            await update.message.reply_text("Игра не начата.")
            return

        session = Session()
        actions = session.query(PlayerAction).filter_by(game_id=self.current_game_id).all()
        if not actions:
            await context.bot.send_message(chat_id=CHANNEL_ID, text="Закупов в текущей игре ещё не было.")
        else:
            if USE_TABLE:
                table = PrettyTable()
                table.field_names = ["Имя", "buy", "quit", "diff"]
                total_buyins = 0
                total_quits = 0
                player_stats = {}

                for action in actions:
                    if action.action == "buyin":
                        total_buyins += action.amount
                        if action.username not in player_stats:
                            player_stats[action.username] = {"buyin": 0, "quit": 0}
                        player_stats[action.username]["buyin"] += action.amount
                    elif action.action == "quit":
                        total_quits += action.amount
                        if action.username not in player_stats:
                            player_stats[action.username] = {"buyin": 0, "quit": 0}
                        player_stats[action.username]["quit"] += action.amount

                for username, stats in player_stats.items():
                    balance = stats["quit"] - stats["buyin"]
                    table.add_row([username, f"{stats['buyin']:.2f}", f"{stats['quit']:.2f}", f"{balance:.2f}"])

                bank_total = total_buyins - total_quits
                summary_text = f"Сводка закупов:\n{table}\n\nТекущая сумма денег в банке: {bank_total:.2f} лева"

                await context.bot.send_message(chat_id=CHANNEL_ID, text=f"<pre>{summary_text}</pre>", parse_mode="HTML")
            else:
                summary_text = "Сводка закупов:\n"
                total_buyins = 0
                total_quits = 0
                player_stats = {}

                for action in actions:
                    if action.action == "buyin":
                        total_buyins += action.amount
                        if action.username not in player_stats:
                            player_stats[action.username] = {"buyin": 0, "quit": 0}
                        player_stats[action.username]["buyin"] += action.amount
                    elif action.action == "quit":
                        total_quits += action.amount
                        if action.username not in player_stats:
                            player_stats[action.username] = {"buyin": 0, "quit": 0}
                        player_stats[action.username]["quit"] += action.amount

                for username, stats in player_stats.items():
                    balance = stats["quit"] - stats["buyin"]
                    summary_text += (f"{username}: закупился на {stats['buyin']:.2f} лева, вышел на {stats['quit']:.2f} лева, "
                                     f"разница: {balance:.2f} лева\n")

                bank_total = total_buyins - total_quits
                summary_text += f"\nТекущая сумма денег в банке: {bank_total:.2f} лева"

                await context.bot.send_message(chat_id=CHANNEL_ID, text=summary_text)
        session.close()

    async def help(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        help_text = (
            "Список команд:\n"
            "/startgame - Начать новую игру.\n"
            "/buyin - Закупить фишки.\n"
            "/quit <фишки> - Выйти из игры, указав количество оставшихся фишек.\n"
            "/endgame - Завершить текущую игру.\n"
            "/summary - Показать сводку текущей игры.\n"
            "/log - Показать лог всех действий.\n"
            "/help - Показать это сообщение."
        )
        await update.message.reply_text(help_text)        

    async def log(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        session = Session()
        actions = session.query(PlayerAction).all()
        log_text = "Лог действий:\n"
        for action in actions:
            timestamp = action.timestamp.replace(tzinfo=timezone.utc)
            formatted_timestamp = self.format_datetime(timestamp)
            amount = f"{action.amount:.2f}" if action.amount is not None else "None"
            log_text += f"{formatted_timestamp}: {action.username} - {action.action} ({action.chips} фишек, {amount} лева)\n"
        session.close()
        await update.message.reply_text(log_text)

    def run(self):
        self.application.run_polling()

if __name__ == "__main__":
    bot = PokerBot()
    bot.run()
