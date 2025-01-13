import json

with open("config.json", "r") as file:
    config = json.load(file)

BOT_TOKEN = config["bot_token"]
CHANNEL_ID = config["channel_id"]
CHIP_VALUE = config["chip_value"]
CHIP_COUNT = config["chip_count"]
TIMEZONE = config["timezone"]
USE_TABLE = config.get("use_table",True)
