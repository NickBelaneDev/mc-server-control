import os
import asyncio
from functools import wraps

from telegram import Update
from telegram.ext import ContextTypes, Application, CommandHandler
from telegram.helpers import escape_markdown

import logging
logger = logging.getLogger(__name__)

from dotenv import load_dotenv, find_dotenv
load_dotenv(find_dotenv())

from ..config_loader import load_config
from ..services import MinecraftServerController
from ..server_log.state_manager import StateManager
from ..server_log.log_watcher import start_watching, stop_watching


def user_is_whitelisted(func):
    """Decorator to check if the user is allowed to execute a command."""
    @wraps(func)
    async def wrapper(update: Update, context: ContextTypes.DEFAULT_TYPE, *args, **kwargs):
        config = context.bot_data.get("config")
        user_id = update.effective_chat.id

        # Allow if whitelist is empty (for initial setup) but log a warning.
        if not config.bot.allowed_chat_ids:
            logger.warning(f"User whitelist is empty. Allowing request from user {user_id}. "
                           f"Please configure 'allowed_chat_ids' in your config.toml for security.")
            return await func(update, context, *args, **kwargs)

        if user_id not in config.bot.allowed_chat_ids:
            logger.warning(f"Unauthorized access attempt by user: {user_id}")
            await context.bot.send_message(chat_id=user_id, text="You are not authorized to use this bot.")
            return

        return await func(update, context, *args, **kwargs)

    return wrapper


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
        
        # Register a callback for the "server ready" event
        # We need a way to know which chat to notify. We'll store it when /start is called.
        self.state_manager.register_ready_callback(self.on_server_ready)

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
        
    async def on_server_ready(self):
        """Async callback triggered by the StateManager when the server is ready."""
        chat_id_to_notify = self.application.bot_data.get("last_chat_id")
        if chat_id_to_notify:
            logger.info(f"Server is ready. Notifying chat_id: {chat_id_to_notify}")
            try:
                await self.application.bot.send_message(
                    chat_id=chat_id_to_notify,
                    text="🚀 Server is ready and accepting players!"
                )
            except Exception as e:
                logger.error(f"Failed to send 'server ready' notification: {e}")

    async def initial_state_sync(self):
        """Checks server status on bot start and syncs state if necessary."""
        if self.msc.is_running:
            logger.info("Server is already running on bot startup. Synchronizing state.")
            await asyncio.sleep(1) # Give log watcher a moment to start
            await asyncio.to_thread(self.msc.run_server_command, "list")

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
    @user_is_whitelisted
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
        
        # Store the chat_id to notify when the server is ready
        context.bot_data["last_chat_id"] = chat_id

    @staticmethod
    @user_is_whitelisted
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
    @user_is_whitelisted
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
        
        escaped_command = escape_markdown(command_to_run, version=2)
        await context.bot.send_message(
            chat_id=chat_id,
            text=f"Executing command: `{escaped_command}`",
            parse_mode='MarkdownV2'
        )
        
        # Run the command on the server asynchronously
        if await asyncio.to_thread(msc.run_server_command, command_to_run):
            await context.bot.send_message(chat_id=chat_id, text="✅ Command executed successfully.")
        else:
            await context.bot.send_message(chat_id=chat_id, text="❌ Failed to execute command. Is the server running correctly?")

    @staticmethod
    @user_is_whitelisted
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
        escaped_player_name = escape_markdown(player_name, version=2)
        await context.bot.send_message(chat_id=chat_id, text=f"Attempting to kick player `{escaped_player_name}`\\.\\.\\.", parse_mode='MarkdownV2')

        success = await asyncio.to_thread(msc.kick_player, player_name)

        if success:
            await context.bot.send_message(chat_id=chat_id, text=f"✅ Player `{escaped_player_name}` kicked\\.", parse_mode='MarkdownV2')
        else:
            await context.bot.send_message(chat_id=chat_id, text=f"❌ Failed to kick player `{escaped_player_name}`\\.", parse_mode='MarkdownV2')

    @staticmethod
    @user_is_whitelisted
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
        escaped_player_name = escape_markdown(player_name, version=2)
        await context.bot.send_message(
            chat_id=chat_id,
            text=f"Attempting to grant operator status to `{escaped_player_name}`\\.\\.\\.",
            parse_mode='MarkdownV2'
        )

        success = await asyncio.to_thread(msc.op_player, player_name)

        if success:
            await context.bot.send_message(chat_id=chat_id, text=f"✅ Player `{escaped_player_name}` is now an operator\\.", parse_mode='MarkdownV2')
        else:
            await context.bot.send_message(chat_id=chat_id, text=f"❌ Failed to grant operator status to `{escaped_player_name}`\\.", parse_mode='MarkdownV2')

    @user_is_whitelisted
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