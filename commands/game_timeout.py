import asyncio
import logging
from datetime import datetime, timezone

from config import CHANNEL_ID, ANNOUNCE_GAME_DURATION
from engine import Session
from domain.entity.game_timeout import GameTimeout
from domain.service.game_timeout_service import CHECK_INTERVAL, check_game_timeout

logger = logging.getLogger(__name__)


async def check_timeouts(application):
    with Session.begin() as session:
        game_id, messages, ended = check_game_timeout(
            session, datetime.now(timezone.utc), ANNOUNCE_GAME_DURATION
        )
    if ended and application.bot_data.get("current_game_id") == game_id:
        application.bot_data.pop("current_game_id", None)
    try:
        for message in messages:
            logger.info("Sending timeout notification: game=%s channel=%s text=%s", game_id, CHANNEL_ID, message)
            await application.bot.send_message(CHANNEL_ID, message)
            logger.info("Timeout notification delivered: game=%s", game_id)
    except Exception:
        logger.exception("Timeout notification failed: game=%s ended=%s", game_id, ended)
        # Never close a game on a warning that Telegram did not receive.
        if not ended and game_id is not None:
            with Session.begin() as session:
                state = session.get(GameTimeout, game_id)
                if state:
                    state.deadline = None
                    state.next_check = datetime.now(timezone.utc)
        raise


async def timeout_loop(application):
    logger.info("Cash-game timeout loop started: poll=300s closure_grace=30min")
    while True:
        try:
            await check_timeouts(application)
        except Exception:
            logger.exception("Cash-game timeout check failed")
        await asyncio.sleep(CHECK_INTERVAL.total_seconds())


async def stop_timeout_loop(application):
    task = application.bot_data.pop("game_timeout_task", None)
    if task:
        logger.info("Stopping cash-game timeout loop")
        task.cancel()
        try:
            await task
        except asyncio.CancelledError:
            pass
