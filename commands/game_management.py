from datetime import datetime, timezone
from database import Session, Game, PlayerAction
from telegram import Update
from telegram.ext import ContextTypes
from prettytable import PrettyTable
from config import CHIP_VALUE, CHIP_COUNT, CHANNEL_ID
from utils import format_datetime
from decorators import restrict_to_channel

class GameManagement:

    @staticmethod
    async def start_game(update: Update, context: ContextTypes.DEFAULT_TYPE):
        session = Session()

        # Проверяем, есть ли незавершённая игра в базе данных
        if "current_game_id" in context.bot_data:
            await update.message.reply_text("Игра уже начата!")
            session.close()
            return

        current_game = session.query(Game).filter_by(end_time=None).first()
        if current_game:
            context.bot_data["current_game_id"] = current_game.id
            await update.message.reply_text("Игра уже начата! Это восстановленная игра.")
            session.close()
            return

        new_game = Game(start_time=datetime.now(timezone.utc))
        session.add(new_game)
        session.commit()

        # Сохраняем game_id в контексте бота
        context.bot_data["current_game_id"] = new_game.id

        # Логируем старт игры
        action = PlayerAction(
            game_id=new_game.id,
            user_id=update.effective_user.id,
            username=update.effective_user.username,
            action="start_game",
            timestamp=datetime.now(timezone.utc)
        )
        session.add(action)
        session.commit()

        session.close()
        await update.message.reply_text("Игра начата! Закупки открыты.")

    @staticmethod
    @restrict_to_channel
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

        # Логируем завершение игры
        action = PlayerAction(
            game_id=current_game.id,
            user_id=update.effective_user.id,
            username=update.effective_user.username,
            action="end_game",
            timestamp=datetime.now(timezone.utc)
        )
        session.add(action)
        session.commit()

        session.close()
        await update.message.reply_text("Игра завершена.")
