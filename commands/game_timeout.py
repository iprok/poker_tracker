import asyncio
import logging
from datetime import datetime, timezone

from config import CHANNEL_ID, ANNOUNCE_GAME_DURATION
from engine import Session
from domain.entity.game_timeout import GameTimeout
from domain.service.game_timeout_service import check_game_timeout

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
            await application.bot.send_message(CHANNEL_ID, message)
    except Exception:
        # Never close a game on a warning that Telegram did not receive.
        if not ended and game_id is not None:
            with Session.begin() as session:
                state = session.get(GameTimeout, game_id)
                if state:
                    state.deadline = None
                    state.next_check = datetime.now(timezone.utc)
        raise


async def timeout_loop(application):
    while True:
        try:
            await check_timeouts(application)
        except Exception:
            logger.exception("Cash-game timeout check failed")
        await asyncio.sleep(60)


async def stop_timeout_loop(application):
    task = application.bot_data.pop("game_timeout_task", None)
    if task:
        task.cancel()
        try:
            await task
        except asyncio.CancelledError:
            pass
