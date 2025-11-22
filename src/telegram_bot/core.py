import os

from telegram import Update
from telegram.ext import ContextTypes, Application, CommandHandler

import logging
logger = logging.getLogger(__name__)

from dotenv import load_dotenv, find_dotenv
load_dotenv(find_dotenv())

from ..config_loader import load_config
from ..services import MinecraftServerController
from ..server_log.state_manager import StateManager
from ..server_log.log_watcher import start_watching, stop_watching


class TelegramBot:
    def __init__(self, token: str, msc: MinecraftServerController, state_manager: StateManager, config: load_config):
        self.msc = msc
        self.state_manager = state_manager
        self.config = config
        self.application = Application.builder().token(token).build()
        self._setup_bot_data()
        self._add_handlers()

    def _setup_bot_data(self):
        """Store components in bot_data for access in handlers."""
        self.application.bot_data["msc"] = self.msc
        self.application.bot_data["state_manager"] = self.state_manager
        self.application.bot_data["config"] = self.config
        self.application.bot_data["watchdog_observer"] = None  # Initialize as not running

    def _add_handlers(self):
        """Set Handlers."""
        start_handler = CommandHandler("start", self.server_start_command)
        stop_handler = CommandHandler("stop", self.server_stop_command)
        help_handler = CommandHandler("help", self.help_command)

        # TODO: Add a /status command that reads from state_manager

        self.application.add_handler(start_handler)
        self.application.add_handler(stop_handler)
        self.application.add_handler(help_handler)

    def run(self):
        """Run the bot."""
        logger.info("Bot running and waiting for messages...")
        self.application.run_polling(poll_interval=1)

    @staticmethod
    async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """Return basic help text."""
        help_txt = """/start    starts the server\n/stop    stops the server\n"""
        await context.bot.send_message(
            chat_id=update.effective_chat.id,
            text=help_txt
        )

    @staticmethod
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

    @staticmethod
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
