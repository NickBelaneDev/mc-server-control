import os
import logging

from dotenv import load_dotenv, find_dotenv

from src.config_loader import load_config
from src.services import MinecraftServerController
from src.server_log.state_manager import StateManager
from src.telegram_bot.core import TelegramBot

logging.basicConfig(level=logging.DEBUG,
                    format="%(asctime)s - %(levelname)s - %(message)s"
                    )

logger = logging.getLogger(__name__)

# Lade Umgebungsvariablen aus der .env-Datei
load_dotenv(find_dotenv())
_TOKEN = os.getenv("BOT_TOKEN")

if __name__ == "__main__":
    if not _TOKEN:
        logger.critical("BOT_TOKEN not found in environment variables. Please check your .env file.")
        exit(1)

    config = load_config()
    msc = MinecraftServerController(config)
    state_manager = StateManager()

    bot = TelegramBot(token=_TOKEN, msc=msc, state_manager=state_manager, config=config)
    bot.run()
