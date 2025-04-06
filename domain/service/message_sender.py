from config import CHANNEL_ID
from telegram import Update
from telegram.ext import ContextTypes


class MessageSender:

    @staticmethod
    def send_to_channel(
        _: Update, context: ContextTypes.DEFAULT_TYPE, text, parse_mode=None
    ):
        return context.bot.send_message(CHANNEL_ID, text, parse_mode=parse_mode)

    @staticmethod
    def send_to_current_channel(
        update: Update,
        _: ContextTypes.DEFAULT_TYPE,
        text,
        reply_markup=None,
        parse_mode=None,
    ):
        if update.message:
            return update.message.reply_text(
                text, reply_markup=reply_markup, parse_mode=parse_mode
            )
        else:
            return None
