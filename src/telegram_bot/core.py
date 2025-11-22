import os
import asyncio

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
        exit_handler = CommandHandler("exit", self.server_exit_command)
        status_handler = CommandHandler("status", self.server_status_command)
        cmd_handler = CommandHandler("cmd", self.server_cmd_command)
        kick_handler = CommandHandler("kick", self.server_kick_command)
        op_handler = CommandHandler("op", self.server_op_command)

        self.application.add_handler(start_handler)
        self.application.add_handler(stop_handler)
        self.application.add_handler(help_handler)
        self.application.add_handler(exit_handler)
        self.application.add_handler(status_handler)
        self.application.add_handler(cmd_handler)
        self.application.add_handler(kick_handler)
        self.application.add_handler(op_handler)

    def run(self):
        """Run the bot."""
        logger.info("Bot running and waiting for messages...")
        self.application.run_polling(poll_interval=1)

    @staticmethod
    async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """Return basic help text."""
        help_txt = (
            "/start    - Starts the Minecraft server\n"
            "/stop     - Stops the Minecraft server\n"
            "/status   - Shows the current server status\n"
            "/cmd      - Executes a command on the server (e.g. /cmd say Hello)\n"
            "/kick     - Kicks a player from the server (e.g. /kick Notch)\n"
            "/op       - Makes a player an operator (e.g. /op Notch)\n"
            "/exit     - Stops the server and the bot"
        )
        await context.bot.send_message(
            chat_id=update.effective_chat.id,
            text=help_txt
        )

    @staticmethod
    def _create_status_message(msc: MinecraftServerController, state_manager: StateManager) -> str:
        """Creates a formatted status message for the server."""
        if not msc.is_running:
            return "🔴 *Server Status: Offline*"

        # If the server is running, get the detailed state
        state = state_manager.get_current_state()

        # Build a nicely formatted message
        status_text = "🟢 *Server Status: Online*\n\n"

        status_text += "✅ Server is ready and accepting players\\.\n" \
            if state.is_ready \
            else "⏳ Server is still starting up\\.\\.\\.\n"

        if state.started_at:
            # MarkdownV2 requires escaping for '-', so we use a backslash.
            start_time_str = state.started_at.strftime("%Y\\-%m\\-%d %H:%M:%S")
            status_text += f"🚀 Started at: {start_time_str}\n"

        player_count = len(state.online_players)
        # Escape parentheses for MarkdownV2
        player_list_str = ", ".join(state.online_players) if state.online_players else "None"
        status_text += f"👥 Players online \\({player_count}\\): {player_list_str}"

        return status_text

    @staticmethod
    async def server_status_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """Provides a formatted status overview of the server."""
        chat_id = update.effective_chat.id
        msc: MinecraftServerController = context.bot_data["msc"]
        state_manager: StateManager = context.bot_data["state_manager"]

        status_text = TelegramBot._create_status_message(msc, state_manager)
        await context.bot.send_message(chat_id=chat_id, text=status_text, parse_mode='MarkdownV2')

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

        await asyncio.to_thread(msc.start)

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

        success = await asyncio.to_thread(msc.stop)

        await context.bot.send_message(
            chat_id=chat_id,
            text="Server Stopped!"
        )

    @staticmethod
    async def server_cmd_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """Executes a command on the Minecraft server console."""
        chat_id = update.effective_chat.id
        msc: MinecraftServerController = context.bot_data["msc"]

        if not msc.is_running:
            await context.bot.send_message(
                chat_id=chat_id,
                text="🔴 Server is not running. Cannot execute command."
            )
            return

        # context.args contains a list of strings, the arguments passed with the command
        if not context.args:
            await context.bot.send_message(
                chat_id=chat_id,
                text="Please provide a command to execute.\nExample: `/cmd say Hello World`",
                parse_mode='MarkdownV2'
            )
            return

        command_to_run = " ".join(context.args)
        
        await context.bot.send_message(
            chat_id=chat_id,
            text=f"Executing command: `{command_to_run}`",
            parse_mode='MarkdownV2'
        )
        
        # Run the command on the server asynchronously
        if await asyncio.to_thread(msc.run_server_command, command_to_run):
            await context.bot.send_message(chat_id=chat_id, text="✅ Command executed successfully.")
        else:
            await context.bot.send_message(chat_id=chat_id, text="❌ Failed to execute command. Is the server running correctly?")

    @staticmethod
    async def server_kick_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """Kicks a player from the server."""
        chat_id = update.effective_chat.id
        msc: MinecraftServerController = context.bot_data["msc"]

        if not msc.is_running:
            await context.bot.send_message(chat_id=chat_id, text="🔴 Server is not running.")
            return

        if not context.args:
            await context.bot.send_message(
                chat_id=chat_id,
                text="Please provide a player name to kick.\nExample: `/kick Notch`",
                parse_mode='MarkdownV2'
            )
            return

        player_name = context.args[0]
        await context.bot.send_message(chat_id=chat_id, text=f"Attempting to kick player `{player_name}`...", parse_mode='MarkdownV2')

        success = await asyncio.to_thread(msc.kick_player, player_name)

        if success:
            await context.bot.send_message(chat_id=chat_id, text=f"✅ Player `{player_name}` kicked.", parse_mode='MarkdownV2')
        else:
            await context.bot.send_message(chat_id=chat_id, text=f"❌ Failed to kick player `{player_name}`.", parse_mode='MarkdownV2')

    @staticmethod
    async def server_op_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """Gives a player operator status."""
        chat_id = update.effective_chat.id
        msc: MinecraftServerController = context.bot_data["msc"]

        if not msc.is_running:
            await context.bot.send_message(chat_id=chat_id, text="🔴 Server is not running.")
            return

        if not context.args:
            await context.bot.send_message(
                chat_id=chat_id,
                text="Please provide a player name to op.\nExample: `/op Notch`",
                parse_mode='MarkdownV2'
            )
            return

        player_name = context.args[0]
        await context.bot.send_message(
            chat_id=chat_id,
            text=f"Attempting to grant operator status to `{player_name}`...",
            parse_mode='MarkdownV2'
        )

        success = await asyncio.to_thread(msc.op_player, player_name)

        if success:
            await context.bot.send_message(chat_id=chat_id, text=f"✅ Player `{player_name}` is now an operator.", parse_mode='MarkdownV2')
        else:
            await context.bot.send_message(chat_id=chat_id, text=f"❌ Failed to grant operator status to `{player_name}`.", parse_mode='MarkdownV2')

    async def server_exit_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """Stops the bot gracefully. The main.py finally block will handle server shutdown."""
        logger.info("Received /exit command. Initiating graceful shutdown.")
        await context.bot.send_message(
            chat_id=update.effective_chat.id,
            text="Shutting down the bot and the server..."
        )
        # This signals run_polling() to stop.
        # The cleanup logic in main.py's finally block will then be executed.
        self.application.stop_running()

        await context.bot.send_message(
            chat_id=update.effective_chat.id,
            text="Server offline."
        )