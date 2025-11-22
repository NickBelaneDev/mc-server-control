import os
import threading
from pathlib import Path

from telegram import Update
from telegram.ext import ContextTypes, Application, ApplicationBuilder, CommandHandler

import logging
logger = logging.getLogger(__name__)

from dotenv import load_dotenv, find_dotenv
load_dotenv(find_dotenv())
_TOKEN = os.getenv("BOT_TOKEN")

from ..config_loader import load_config
from ..services import MinecraftServerController
from ..server_log.state_manager import StateManager
from ..server_log.log_watcher import start_watching, stop_watching


async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Return basic help text."""
    chat_id = update.effective_chat.id

    help_txt = """/start    starts the server\n/stop    stops the server\n"""

    await context.bot.send_message(
        chat_id=chat_id,
        text=help_txt
    )


async def server_start_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Starts the minecraft server."""
    chat_id = update.effective_chat.id
    msc: MinecraftServerController = context.bot_data["msc"]
    if msc.is_running:
        await context.bot.send_message(
            chat_id=chat_id,
            text="Server is already running!"
        )
        return


    await context.bot.send_message(
        chat_id=chat_id,
        text="Starting the server..."
    )

    msc.start()

    # Start the log watcher after the server starts
    config = context.bot_data["config"]
    state_manager = context.bot_data["state_manager"]
    observer = start_watching(str(config.full_log_path), state_manager)
    context.bot_data["watchdog_observer"] = observer

    await context.bot.send_message(
        chat_id=chat_id,
        text="Server started!"
    )


async def server_stop_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Stops the minecraft server."""
    chat_id = update.effective_chat.id
    msc: MinecraftServerController = context.bot_data["msc"]

    if not msc.is_running:
        await context.bot.send_message(
            chat_id=chat_id,
            text="Server is not running!"
        )
        return

    await context.bot.send_message(
        chat_id=chat_id,
        text="Stopping the server..."
    )

    # Stop the log watcher before stopping the server
    observer = context.bot_data.get("watchdog_observer")
    if observer:
        stop_watching(observer)
        context.bot_data["watchdog_observer"] = None

    msc.stop()

    await context.bot.send_message(
        chat_id=chat_id,
        text="Server Stopped!"
    )

def main() -> None:
    # 1. Load Config and create main components
    config = load_config()
    msc = MinecraftServerController(config)
    state_manager = StateManager()

    """Run the bot."""
    application = Application.builder().token(_TOKEN).build()

    # 2. Store components in bot_data for access in handlers
    application.bot_data["msc"] = msc
    application.bot_data["state_manager"] = state_manager
    application.bot_data["config"] = config
    application.bot_data["watchdog_observer"] = None # Initialize as not running

    """Set Handlers."""
    start_handler = CommandHandler("start", server_start_command)
    stop_handler = CommandHandler("stop", server_stop_command)
    help_handler = CommandHandler("help", help_command)

    # TODO: Add a /status command that reads from state_manager

    application.add_handler(start_handler)
    application.add_handler(stop_handler)
    application.add_handler(help_handler)

    logger.info("Bot running and waiting for messages...")
    application.run_polling(poll_interval=1)

if __name__ == "__main__":
    main()
