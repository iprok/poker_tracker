"""Characterization tests: real handlers and SQLite, no Telegram connection."""

import os
import json
import tempfile
import sys
import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import AsyncMock, patch


def setUpModule():
    # Application imports read config.json and create a relative SQLite engine.
    # Enter a disposable directory BEFORE importing any application module.
    global engine, Game, PlayerAction, PlayerActions, GameManagement
    if "engine" in sys.modules or "config" in sys.modules:
        raise RuntimeError(
            "Run this suite in a fresh process: application already imported"
        )
    network = patch(
        "socket.socket.connect",
        side_effect=AssertionError("Network forbidden in tests"),
    )
    network.start()
    unittest.addModuleCleanup(network.stop)
    original = Path.cwd()
    temporary = tempfile.TemporaryDirectory(prefix="poker-tests-")
    unittest.addModuleCleanup(temporary.cleanup)
    unittest.addModuleCleanup(os.chdir, original)
    os.chdir(temporary.name)
    Path("config.json").write_text(
        json.dumps(
            {
                "bot_token": "123456:TEST_ONLY",
                "channel_id": -1001,
                "channel_tournament_id": -1002,
                "chip_value": 1,
                "chip_count": 3000,
                "currency": "EUR",
                "timezone": "UTC",
                "show_summary_on_buyin": True,
                "show_summary_on_quit": True,
                "admin_ids": [101],
            }
        )
    )
    import engine

    # Same import order as bot_main: handlers before db_init.
    from commands.game_management import GameManagement
    from commands.player_actions import PlayerActions
    from domain.entity.game import Game
    from domain.entity.player_action import PlayerAction
    from db_init import init_db

    init_db()
    unittest.addModuleCleanup(engine.Engine.dispose)
    unittest.addModuleCleanup(engine.session.close)


class CashGameTests(unittest.IsolatedAsyncioTestCase):
    def setUp(self):
        self.assertTrue(Path.cwd().name.startswith("poker-tests-"))
        engine.Base.metadata.drop_all(engine.Engine)
        engine.Base.metadata.create_all(engine.Engine)
        self.update = SimpleNamespace(
            effective_user=SimpleNamespace(id=101, username="alice"),
            effective_chat=SimpleNamespace(type="private"),
            message=SimpleNamespace(text="", reply_text=AsyncMock()),
        )

        async def get_chat(user_id):
            return SimpleNamespace(
                first_name={101: "Alice", 102: "Bob"}[user_id],
                last_name=None,
                username=None,
            )

        self.context = SimpleNamespace(
            bot_data={},
            user_data={},
            args=[],
            bot=SimpleNamespace(
                send_message=AsyncMock(),
                get_chat=AsyncMock(side_effect=get_chat),
                get_chat_member=AsyncMock(
                    return_value=SimpleNamespace(status="member")
                ),
            ),
        )

    def actions(self, kind):
        with engine.Session() as session:
            return (
                session.query(PlayerAction)
                .filter_by(action=kind)
                .order_by(PlayerAction.id)
                .all()
            )

    def replies(self):
        return "\n".join(
            str(call.args[0]) for call in self.update.message.reply_text.await_args_list
        )

    async def start_and_buy(self, count=1):
        await GameManagement.start_game(self.update, self.context)
        for _ in range(count):
            await PlayerActions.buyin(self.update, self.context)

    async def withdraw(self, chips):
        self.context.args = [str(chips)]
        await PlayerActions.quit(self.update, self.context)

    async def test_buyin_requires_started_game(self):
        await PlayerActions.buyin(self.update, self.context)
        self.assertEqual(self.actions("buyin"), [])
        self.assertIn("/startgame", self.replies())

    async def test_repeated_buyins_are_persisted_and_reported(self):
        await self.start_and_buy(2)
        self.assertEqual(
            [(a.chips, a.amount) for a in self.actions("buyin")], [(3000, 1), (3000, 1)]
        )
        self.assertIn("2 раз(а) на общую сумму 2.00 EUR", self.replies())
        self.assertTrue(self.context.bot.send_message.await_count > 0)

    async def test_start_is_idempotent_and_restores_game_after_context_loss(self):
        await GameManagement.start_game(self.update, self.context)
        game_id = self.context.bot_data["current_game_id"]
        await GameManagement.start_game(self.update, self.context)
        self.context.bot_data.clear()
        await GameManagement.start_game(self.update, self.context)
        self.assertEqual(self.context.bot_data["current_game_id"], game_id)
        self.assertEqual(len(self.actions("start_game")), 1)
        self.assertIn("восстановленная игра", self.replies())

    async def test_zero_exit_records_loss(self):
        await self.start_and_buy()
        await self.withdraw(0)
        self.assertEqual(self.actions("quit")[0].amount, 0)
        self.assertIn("Вы должны в банк 1.0 EUR", self.replies())

    async def test_exit_at_buyin_value_has_zero_balance(self):
        await self.start_and_buy()
        await self.withdraw(3000)
        self.assertEqual(self.actions("quit")[0].amount, 1)
        self.assertIn("Никто никому ничего не должен", self.replies())

    async def test_two_player_settlement_and_summary(self):
        await self.start_and_buy()
        self.update.effective_user = SimpleNamespace(id=102, username="bob")
        await PlayerActions.buyin(self.update, self.context)
        await self.withdraw(4500)
        self.assertIn("Банк должен вам 0.5 EUR", self.replies())
        self.update.effective_user = SimpleNamespace(id=101, username="alice")
        await self.withdraw(1500)
        self.assertEqual(sum(a.amount for a in self.actions("quit")), 2)
        with engine.Session() as session:
            summary = await PlayerActions.summary_formatter(
                session.query(PlayerAction).all(),
                session.query(Game).one(),
                self.context,
            )
        self.assertIn("Alice: 0.50 EUR", summary.split("Банк должен:")[0])
        self.assertIn("Bob: 0.50 EUR", summary.split("Банк должен:")[1])
        self.assertIn("денег в банке:</b> 0.00 EUR", summary)

    async def test_invalid_exits_do_not_write(self):
        await self.start_and_buy()
        for chips, message in [
            (-1500, "меньше 0"),
            (1, "кратно 1500"),
            (4500, "больше доступных"),
        ]:
            with self.subTest(chips=chips):
                self.update.message.reply_text.reset_mock()
                await self.withdraw(chips)
                self.assertEqual(self.actions("quit"), [])
                self.assertIn(message, self.replies())

    async def test_previous_exits_reduce_available_bank(self):
        await self.start_and_buy()
        await self.withdraw(1500)
        await self.withdraw(3000)
        self.assertEqual(len(self.actions("quit")), 1)
        self.assertIn("доступных в банке: 1500", self.replies())

    async def test_quit_confirmation_records_only_once(self):
        await self.start_and_buy()
        self.update.message.text = "/quit 1500"
        await PlayerActions.handle_quit_command(self.update, self.context)
        self.assertEqual(self.actions("quit"), [])
        self.update.message.text = "Да, вывести 1500"
        await PlayerActions.handle_confirmation(self.update, self.context)
        await PlayerActions.handle_confirmation(self.update, self.context)
        self.assertEqual(len(self.actions("quit")), 1)
        self.assertNotIn("pending_quit_amount", self.context.user_data)

    async def test_cancel_quit_does_not_write(self):
        await self.start_and_buy()
        self.update.message.text = "/quit 1500"
        await PlayerActions.handle_quit_command(self.update, self.context)
        self.update.message.text = "Нет, отменить"
        await PlayerActions.handle_confirmation(self.update, self.context)
        self.assertEqual(self.actions("quit"), [])
        self.assertNotIn("pending_quit_amount", self.context.user_data)

    async def test_end_confirmation_and_next_game(self):
        await self.start_and_buy()
        self.update.message.text = "/endgame"
        await GameManagement.handle_endgame_command(self.update, self.context)
        self.update.message.text = "Нет, продолжить играть"
        await GameManagement.handle_confirmation(self.update, self.context)
        self.assertEqual(self.actions("end_game"), [])
        self.update.message.text = "/endgame"
        await GameManagement.handle_endgame_command(self.update, self.context)
        self.update.message.text = "Да, завершить игру"
        await GameManagement.handle_confirmation(self.update, self.context)
        self.assertNotIn("current_game_id", self.context.bot_data)
        self.assertNotIn("pending_endgame", self.context.user_data)
        self.assertEqual(len(self.actions("end_game")), 1)
        with engine.Session() as session:
            self.assertIsNotNone(session.query(Game).one().end_time)
        await PlayerActions.buyin(self.update, self.context)
        self.assertEqual(len(self.actions("buyin")), 1)
        await GameManagement.start_game(self.update, self.context)
        await PlayerActions.buyin(self.update, self.context)
        self.assertNotEqual(
            self.actions("buyin")[0].game_id, self.actions("buyin")[1].game_id
        )

    async def test_nonmember_or_group_chat_cannot_buy(self):
        await self.start_and_buy()
        for member, chat_type in [("left", "private"), ("member", "group")]:
            with self.subTest(member=member, chat_type=chat_type):
                self.context.bot.get_chat_member.return_value = SimpleNamespace(
                    status=member
                )
                self.update.effective_chat.type = chat_type
                await PlayerActions.buyin(self.update, self.context)
                self.assertEqual(len(self.actions("buyin")), 1)

    async def test_exit_without_buyin_in_current_game_is_rejected(self):
        # Alice's previous-game buyin must not authorize an exit in the next game.
        await self.start_and_buy()
        await GameManagement.end_game(self.update, self.context)
        await GameManagement.start_game(self.update, self.context)
        self.update.effective_user = SimpleNamespace(id=102, username="bob")
        await PlayerActions.buyin(self.update, self.context)
        self.update.effective_user = SimpleNamespace(id=101, username="alice")
        for chips in (0, 1500):
            with self.subTest(chips=chips):
                await self.withdraw(chips)
                self.assertEqual(self.actions("quit"), [])
                self.assertIn("нет закупов в текущей игре", self.replies())

    async def test_buyin_and_exit_restore_game_without_start_command(self):
        await self.start_and_buy()
        game_id = self.context.bot_data["current_game_id"]
        self.context.bot_data.clear()
        await PlayerActions.buyin(self.update, self.context)
        self.assertEqual(self.context.bot_data["current_game_id"], game_id)
        self.context.bot_data.clear()
        await self.withdraw(1500)
        self.assertEqual(self.actions("quit")[0].game_id, game_id)
        self.assertEqual(len(self.actions("start_game")), 1)
        self.assertEqual(len(self.actions("buyin")), 2)

    async def test_cancel_end_clears_confirmation(self):
        await self.start_and_buy()
        self.update.message.text = "/endgame"
        await GameManagement.handle_endgame_command(self.update, self.context)
        self.update.message.text = "Нет, продолжить играть"
        await GameManagement.handle_confirmation(self.update, self.context)
        self.assertNotIn("pending_endgame", self.context.user_data)
        self.update.message.text = "Да, завершить игру"
        await GameManagement.handle_confirmation(self.update, self.context)
        self.assertEqual(self.actions("end_game"), [])

    async def test_application_builds_on_python314_without_network(self):
        from bot_main import build_application, post_init

        application = build_application()
        self.assertIs(application.post_init, post_init)
        self.assertEqual(application.bot.token, "123456:TEST_ONLY")

    async def format_test_summary(self, actions):
        from datetime import datetime, timezone

        game = Game(start_time=datetime.now(timezone.utc))
        return await PlayerActions.summary_formatter(actions, game, self.context)

    async def test_summary_keeps_namesakes_in_separate_balance_groups(self):
        self.context.bot.get_chat.side_effect = lambda user_id: SimpleNamespace(
            first_name="Alex",
            last_name=None,
            username="alice" if user_id == 101 else None,
        )
        actions = [
            PlayerAction(user_id=101, username="Alex", action="buyin", amount=1),
            PlayerAction(user_id=102, username="Alex", action="buyin", amount=1),
            PlayerAction(user_id=102, username="Alex", action="quit", amount=2),
        ]
        summary = await self.format_test_summary(actions)
        debtors, creditors = summary.split("💰 <b>Банк должен:</b>")
        self.assertIn("Alex (@alice): 1.00 EUR", debtors)
        self.assertIn("Alex (ID 102): 1.00 EUR", creditors)
        self.assertIn("денег в банке:</b> 0.00 EUR", summary)

    async def test_summary_combines_renamed_player_when_telegram_unavailable(self):
        self.context.bot.get_chat.side_effect = RuntimeError("Unavailable")
        actions = [
            PlayerAction(user_id=101, username="Old name", action="buyin", amount=1),
            PlayerAction(user_id=101, username="New name", action="quit", amount=1),
        ]
        summary = await self.format_test_summary(actions)
        self.assertIn("Обрели гармонию", summary)
        self.assertIn("Old name: 0.00 EUR", summary)
        self.assertNotIn("Должны банку", summary)
        self.assertNotIn("Банк должен:", summary)
        self.context.bot.get_chat.assert_awaited_once_with(101)

    async def test_summary_uses_ids_for_unavailable_namesakes(self):
        self.context.bot.get_chat.side_effect = RuntimeError("Unavailable")
        actions = [
            PlayerAction(user_id=user_id, username="Alex", action="buyin", amount=1)
            for user_id in (101, 102)
        ]
        summary = await self.format_test_summary(actions)
        self.assertIn("Alex (ID 101): 1.00 EUR", summary)
        self.assertIn("Alex (ID 102): 1.00 EUR", summary)

    def timeout_check(self, minutes, announce=False):
        from datetime import datetime, timedelta, timezone
        from domain.service.game_timeout_service import check_game_timeout

        with engine.Session.begin() as session:
            return check_game_timeout(
                session,
                datetime(2026, 1, 1, tzinfo=timezone.utc) + timedelta(minutes=minutes),
                announce,
            )

    def timed_game(self, amount=0):
        from datetime import datetime, timezone

        with engine.Session.begin() as session:
            game = Game(start_time=datetime(2026, 1, 1, tzinfo=timezone.utc))
            session.add(game)
            session.flush()
            if amount:
                session.add(
                    PlayerAction(
                        game_id=game.id,
                        user_id=101,
                        action="buyin",
                        amount=amount,
                        chips=3000,
                    )
                )
            return game.id

    def test_timeout_warns_then_closes_low_bank(self):
        self.timed_game(1)
        self.assertEqual(self.timeout_check(29)[1], [])
        self.assertIn("меньше 2 евро", self.timeout_check(30)[1][0])
        self.assertFalse(self.timeout_check(59)[2])
        self.assertTrue(self.timeout_check(60)[2])
        self.assertEqual(len(self.actions("end_game")), 1)
        self.assertEqual(self.timeout_check(90)[1], [])

    def test_timeout_buyin_cancels_low_bank_closure(self):
        self.timed_game(1)
        self.timeout_check(30)
        self.execute_buyin()
        self.assertFalse(self.timeout_check(60)[2])
        self.assertFalse(self.timeout_check(90)[2])
        self.assertEqual(self.actions("end_game"), [])

    def test_timeout_duration_threshold_and_repeated_extensions(self):
        self.timed_game(10)
        self.assertEqual(self.timeout_check(720)[1], [])
        self.assertIn("12 часов", self.timeout_check(750)[1][0])
        self.execute_buyin()
        self.assertFalse(self.timeout_check(780)[2])
        self.execute_buyin()
        self.assertFalse(self.timeout_check(810)[2])
        self.assertTrue(self.timeout_check(840)[2])

    def test_timeout_notifications_are_optional_and_two_euros_is_safe(self):
        self.timed_game(2)
        self.assertEqual(self.timeout_check(30)[1], [])
        self.assertIn("1 ч 0 мин", self.timeout_check(60, True)[1][0])
        self.assertEqual(self.actions("end_game"), [])

    def test_timeout_buyin_then_exit_still_extends(self):
        game_id = self.timed_game(1)
        self.timeout_check(30)
        self.execute_buyin()
        with engine.Session.begin() as session:
            session.add(
                PlayerAction(
                    game_id=game_id, user_id=101, action="quit", amount=1, chips=3000
                )
            )
        self.assertFalse(self.timeout_check(60)[2])
        self.assertTrue(self.timeout_check(90)[2])

    def test_timeout_ignores_manually_finished_game(self):
        from datetime import datetime, timezone

        game_id = self.timed_game(1)
        self.timeout_check(30)
        with engine.Session.begin() as session:
            session.get(Game, game_id).end_time = datetime.now(timezone.utc)
        self.assertEqual(self.timeout_check(60)[1], [])
        self.assertEqual(self.actions("end_game"), [])

    async def test_timeout_failed_warning_is_retried_before_closing(self):
        from commands.game_timeout import check_timeouts
        from domain.entity.game_timeout import GameTimeout

        game_id = self.timed_game(1)
        self.context.bot.send_message.side_effect = RuntimeError("Telegram unavailable")
        with self.assertRaisesRegex(RuntimeError, "Telegram unavailable"):
            await check_timeouts(self.context)
        with engine.Session() as session:
            self.assertIsNone(session.get(GameTimeout, game_id).deadline)
            self.assertIsNone(session.get(Game, game_id).end_time)
        self.context.bot.send_message.side_effect = None
        await check_timeouts(self.context)
        with engine.Session() as session:
            self.assertIsNotNone(session.get(GameTimeout, game_id).deadline)
            self.assertIsNone(session.get(Game, game_id).end_time)

    async def test_timeout_completion_clears_context_after_restart(self):
        from commands.game_timeout import check_timeouts

        game_id = self.timed_game(1)
        self.timeout_check(30)
        self.context.bot_data["current_game_id"] = game_id
        await check_timeouts(self.context)
        self.assertNotIn("current_game_id", self.context.bot_data)
        self.assertEqual(len(self.actions("end_game")), 1)
        self.assertIn(
            "автоматически завершена", self.context.bot.send_message.await_args.args[1]
        )

    def execute_buyin(self, user_id=101):
        from domain.repository.game_repository import GameRepository
        from domain.repository.player_action_repository import PlayerActionRepository
        from domain.use_cases.Cash.buyin_use_case import BuyinUseCase

        with engine.Session.begin() as session:
            return BuyinUseCase(
                GameRepository(session), PlayerActionRepository(session), 3000, 1
            ).execute(user_id, "Player")

    def create_game(self):
        with engine.Session.begin() as session:
            game = Game()
            session.add(game)
            session.flush()
            return game.id

    def test_buyin_scenario_rejects_missing_active_game(self):
        from domain.use_cases.Cash.buyin_use_case import NoActiveGameError

        with self.assertRaises(NoActiveGameError):
            self.execute_buyin()
        self.assertEqual(self.actions("buyin"), [])

    def test_buyin_scenario_first_and_repeat(self):
        game_id = self.create_game()
        first = self.execute_buyin()
        second = self.execute_buyin()
        self.assertEqual((first.game_id, first.chips, first.amount), (game_id, 3000, 1))
        self.assertEqual((first.buyin_count, first.buyin_total), (1, 1))
        self.assertEqual((second.buyin_count, second.buyin_total), (2, 2))
        self.assertEqual(len(self.actions("buyin")), 2)

    def test_buyin_scenario_totals_are_scoped_to_player_and_game(self):
        from datetime import datetime, timezone

        game_id = self.create_game()
        self.execute_buyin(101)
        self.execute_buyin(101)
        other = self.execute_buyin(102)
        self.assertEqual((other.buyin_count, other.buyin_total), (1, 1))
        with engine.Session.begin() as session:
            session.get(Game, game_id).end_time = datetime.now(timezone.utc)
        next_id = self.create_game()
        result = self.execute_buyin(101)
        self.assertEqual(
            (result.game_id, result.buyin_count, result.buyin_total), (next_id, 1, 1)
        )

    def test_buyin_scenario_rolls_back_if_totals_fail(self):
        from domain.repository.player_action_repository import PlayerActionRepository

        self.create_game()
        with patch.object(
            PlayerActionRepository,
            "get_game_buyin_totals",
            side_effect=RuntimeError("Database failure"),
        ):
            with self.assertRaisesRegex(RuntimeError, "Database failure"):
                self.execute_buyin()
        self.assertEqual(self.actions("buyin"), [])


class PollingStartupTests(unittest.TestCase):
    def test_polling_creates_event_loop_on_python314(self):
        import asyncio
        from bot_main import build_application
        from telegram.ext import Application

        asyncio.set_event_loop(None)
        application = build_application()

        async def stop_after_init(app):
            app.stop_running()

        application.post_init = stop_after_init
        with patch.object(
            Application, "initialize", new_callable=AsyncMock
        ) as initialize:
            application.run_polling(stop_signals=None)
        initialize.assert_awaited_once()
        asyncio.set_event_loop(None)
