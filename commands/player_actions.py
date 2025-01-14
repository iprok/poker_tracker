from datetime import datetime, timezone
from database import Session, PlayerAction
from telegram import Update
from telegram.ext import ContextTypes
from sqlalchemy.sql import func
from utils import format_datetime
from config import CHIP_VALUE, CHIP_COUNT

class PlayerActions:

    @staticmethod
    async def buyin(update: Update, context: ContextTypes.DEFAULT_TYPE):
        session = Session()
        current_game_id = context.bot_data.get("current_game_id")

        if current_game_id is None:
            await update.message.reply_text("Сначала начните игру командой /startgame.")
            session.close()
            return

        user = update.effective_user
        action = PlayerAction(
            game_id=current_game_id,
            user_id=user.id,
            username=user.username,
            action="buyin",
            chips=CHIP_COUNT,
            amount=CHIP_VALUE,
            timestamp=datetime.now(timezone.utc)
        )
        session.add(action)
        session.commit()
        session.close()

        await update.message.reply_text(f"Закуп на {CHIP_COUNT} фишек ({CHIP_VALUE} лева) записан.")

    @staticmethod
    async def quit(update: Update, context: ContextTypes.DEFAULT_TYPE):
        session = Session()
        current_game_id = context.bot_data.get("current_game_id")

        if current_game_id is None:
            await update.message.reply_text("Сначала начните игру командой /startgame.")
            session.close()
            return

        total_buyins = session.query(PlayerAction).filter_by(
            game_id=current_game_id, action="buyin"
        ).count() * CHIP_COUNT

        total_quits = session.query(PlayerAction).filter_by(
            game_id=current_game_id, action="quit"
        ).with_entities(func.sum(PlayerAction.chips)).scalar() or 0

        max_chips = total_buyins - total_quits

        try:
            if not context.args:
                raise ValueError("Вы не указали количество фишек. Пример: /quit 1500")

            chips_left = int(context.args[0])
            if chips_left < 25:
                raise ValueError("Количество фишек не может быть меньше 25.")
            if chips_left > max_chips:
                raise ValueError(f"Количество фишек не может быть больше доступных в банке: {max_chips}.")
        except (ValueError, IndexError) as e:
            await update.message.reply_text(f"Ошибка: {e}")
            session.close()
            return

        amount = (chips_left / CHIP_COUNT) * CHIP_VALUE
        user = update.effective_user
        action = PlayerAction(
            game_id=current_game_id,
            user_id=user.id,
            username=user.username,
            action="quit",
            chips=chips_left,
            amount=amount,
            timestamp=datetime.now(timezone.utc)
        )
        session.add(action)
        session.commit()
        session.close()

        await update.message.reply_text(f"Выход записан. У вас осталось {chips_left} фишек, что эквивалентно {amount:.2f} лева.")

    @staticmethod
    async def log(update: Update, context: ContextTypes.DEFAULT_TYPE):
        session = Session()
        actions = session.query(PlayerAction).all()
        log_text = "Лог действий:\n"
        for action in actions:
            formatted_timestamp = format_datetime(action.timestamp)
            amount = f"{action.amount:.2f}" if action.amount is not None else "None"
            log_text += f"{formatted_timestamp}: {action.username} - {action.action} ({action.chips} фишек, {amount} лева)\n"
        session.close()
        await update.message.reply_text(log_text)

    @staticmethod
    async def help(update: Update, context: ContextTypes.DEFAULT_TYPE):
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
