import os
import logging
import asyncio

from dotenv import load_dotenv, find_dotenv

from src.config_loader import load_config
from src.services import MinecraftServerController
from src.server_log.state_manager import StateManager
from src.telegram_bot.core import TelegramBot
from src.server_log.log_watcher import stop_watching


logging.basicConfig(level=logging.INFO,
                    format="%(asctime)s - %(levelname)s - %(message)s"
                    )

logger = logging.getLogger(__name__)

# Load environmental variables from .env
load_dotenv(find_dotenv())
_TOKEN = os.getenv("BOT_TOKEN")

async def main():
    if not _TOKEN:
        logger.critical("BOT_TOKEN not found in environment variables. Please check your .env file.")
        exit(1)
    
    config = load_config()
    msc = MinecraftServerController(config.mc)
    state_manager = StateManager()
    
    bot = TelegramBot(token=_TOKEN, msc=msc, state_manager=state_manager, config=config)
    
    try:
        await bot.application.initialize() # Runs post_init
        await bot.initial_state_sync()
        await bot.application.start()
        await bot.application.updater.start_polling()
        # Keep the script running until shutdown is signaled
        while bot.application.updater.is_running:
            await asyncio.sleep(1)
            
    except (KeyboardInterrupt, SystemExit):
        logger.info("Shutdown signal received. Stopping services...")
    
    finally:
        if bot.application.updater.is_running:
            await bot.application.updater.stop()
        if bot.application.running:
            await bot.application.stop()
            
        # Ensure a clean shutdown of the Minecraft server and watchdog
        if msc.is_running:
            logger.info("Minecraft server is running, initiating shutdown.")
            # Stop the log watcher before stopping the server
            observer = bot.application.bot_data.get("watchdog_observer")
            if observer:
                stop_watching(observer)
            
            await asyncio.to_thread(msc.stop)
            logger.info("Minecraft server stopped.")
        logger.info("Application has been shut down gracefully.")

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except (KeyboardInterrupt, SystemExit):
        logger.info("Application exiting.")
