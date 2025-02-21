import json

with open("config.json", "r") as file:
    config = json.load(file)

BOT_TOKEN = config["bot_token"]
CHANNEL_ID = config["channel_id"]
CHIP_VALUE = config["chip_value"]
CHIP_COUNT = config["chip_count"]
TIMEZONE = config["timezone"]
USE_TABLE = config.get("use_table", True)
SHOW_SUMMARY_ON_BUYIN = config["show_summary_on_buyin"]
SHOW_SUMMARY_ON_QUIT = config["show_summary_on_quit"]
LOG_AMOUNT_LAST_GAMES = config.get("log_amount_last_games", 3)
LOG_AMOUNT_LAST_ACTIONS = config.get("log_amount_last_actions", 20)
