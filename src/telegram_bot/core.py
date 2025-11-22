import os

from telegram import Update
from telegram.ext import ContextTypes, Application, ApplicationBuilder, CommandHandler

import logging
logger = logging.getLogger(__name__)

from dotenv import load_dotenv, find_dotenv
load_dotenv(find_dotenv())
_TOKEN = os.getenv("BOT_TOKEN")

from ..config_loader import load_config
from ..services import MinecraftServerController

#TODO: Remove that later and put the condition into the MinecraftServerController Class.
server_status = {           # TO BE REMOVED
    "is_running": False
}

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

    if server_status["is_running"]: # TO BE REMOVED
        await context.bot.send_message(
            chat_id=chat_id,
            text="Server is already running!"
        )
        return

    msc = context.bot_data["msc"]
    await context.bot.send_message(
        chat_id=chat_id,
        text="Starting the server..."
    )

    msc.start()

    await context.bot.send_message(
        chat_id=chat_id,
        text="Server started!"
    )
    server_status["is_running"] = True

async def server_stop_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Stops the minecraft server."""
    chat_id = update.effective_chat.id

    if not server_status["is_running"]:# TO BE REMOVED
        await context.bot.send_message(
            chat_id=chat_id,
            text="Server is not running!"
        )
        return

    msc = context.bot_data["msc"]
    await context.bot.send_message(
        chat_id=chat_id,
        text="Stopping the server..."
    )

    msc.stop()

    await context.bot.send_message(
        chat_id=chat_id,
        text="Server Stopped!"
    )
    server_status["is_running"] = False

def main() -> None:
    msc = MinecraftServerController(load_config())

    """Run the bot."""
    application = Application.builder().token(_TOKEN).build()

    """Fill the Bot with data."""
    application.bot_data["msc"] = msc

    """Set Handlers."""
    start_handler = CommandHandler("start", server_start_command)
    stop_handler = CommandHandler("stop", server_stop_command)
    help_handler = CommandHandler("help", help_command)

    application.add_handler(start_handler)
    application.add_handler(stop_handler)
    application.add_handler(help_handler)

    logger.info("Bot running and waiting vor messages...")
    application.run_polling(poll_interval=1)

if __name__ == "__main__":
    main()
