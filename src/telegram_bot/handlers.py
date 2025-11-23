import asyncio
import logging
from functools import wraps
from typing import Callable

from telegram import Update
from telegram.ext import ContextTypes
from telegram.helpers import escape_markdown

from ..config_models import AppConfig
from ..services import MinecraftServerController
from ..server_log.state_manager import StateManager
from ..server_commands import ServerCommand
from ..server_log.log_watcher import start_watching, stop_watching

logger = logging.getLogger(__name__)

# --- Decorators for Command Handlers ---

def user_is_whitelisted(func: Callable) -> Callable:
    """Decorator to check if the user is allowed to execute a command."""
    @wraps(func)
    async def wrapper(update: Update, context: ContextTypes.DEFAULT_TYPE, *args, **kwargs):
        config: AppConfig = context.bot_data["config"]
        user_id = update.effective_chat.id

        if user_id not in config.bot.allowed_chat_ids:
            logger.warning(f"Unauthorized access attempt by user: {user_id}")
            await context.bot.send_message(chat_id=user_id, text="You are not authorized to use this bot.")
            return
        return await func(update, context, *args, **kwargs)
    return wrapper

def require_server_running(func: Callable) -> Callable:
    """Decorator to ensure the server is running before executing a command."""
    @wraps(func)
    async def wrapper(update: Update, context: ContextTypes.DEFAULT_TYPE, *args, **kwargs):
        msc: MinecraftServerController = context.bot_data["msc"]
        if not msc.is_running:
            await context.bot.send_message(
                chat_id=update.effective_chat.id,
                text="🔴 Server is not running. Please start it first with /start."
            )
            return
        return await func(update, context, *args, **kwargs)
    return wrapper

def require_args(count: int, message: str) -> Callable:
    """Decorator to check if a command received a specific number of arguments."""
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        async def wrapper(update: Update, context: ContextTypes.DEFAULT_TYPE, *args, **kwargs):
            if len(context.args) < count:
                await context.bot.send_message(
                    chat_id=update.effective_chat.id,
                    text=message,
                    parse_mode='MarkdownV2'
                )
                return
            return await func(update, context, *args, **kwargs)
        return wrapper
    return decorator

# --- Command Handler Functions ---

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Displays a list of available commands."""
    help_text = (
        "/start    - Starts the Minecraft server\n"
        "/stop     - Stops the Minecraft server\n"
        "/status   - Shows the current server status\n"
        "/cmd      - Executes a command on the server \\(e\\.g\\., `/cmd say Hello`\\)\n"
        "/kick     - Kicks a player \\(e\\.g\\., `/kick Notch`\\)\n"
        "/op       - Makes a player an operator \\(e\\.g\\., `/op Notch`\\)\n"
        "/exit     - Stops the server and the bot"
    )
    await context.bot.send_message(
        chat_id=update.effective_chat.id,
        text=help_text,
        parse_mode='MarkdownV2'
    )

def _create_status_message(msc: MinecraftServerController, state_manager: StateManager) -> str:
    """Helper function to create a formatted server status message."""
    if not msc.is_running:
        return "🔴 *Server Status: Offline*"

    state = state_manager.get_current_state()
    status_text = "🟢 *Server Status: Online*\n\n"
    status_text += "✅ Server is ready and accepting players\\.\n" if state.is_ready else "⏳ Server is still starting up\\.\\.\\.\n"

    if state.started_at:
        start_time_str = state.started_at.strftime("%Y\\-%m\\-%d %H:%M:%S")
        status_text += f"🚀 Started at: {start_time_str}\n"

    player_count = len(state.online_players)
    player_list_str = escape_markdown(", ".join(state.online_players) if state.online_players else "None", version=2)
    status_text += f"👥 Players online \\({player_count}\\): {player_list_str}"
    return status_text

@user_is_whitelisted
async def server_status_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Provides a formatted status overview of the server."""
    msc: MinecraftServerController = context.bot_data["msc"]
    state_manager: StateManager = context.bot_data["state_manager"]
    status_text = _create_status_message(msc, state_manager)
    await context.bot.send_message(chat_id=update.effective_chat.id, text=status_text, parse_mode='MarkdownV2')

@user_is_whitelisted
async def server_start_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Starts the Minecraft server."""
    msc: MinecraftServerController = context.bot_data["msc"]
    if msc.is_running:
        await context.bot.send_message(chat_id=update.effective_chat.id, text="Server is already running!")
        return

    await context.bot.send_message(chat_id=update.effective_chat.id, text="Starting the server...")
    await asyncio.to_thread(msc.start)

    config: AppConfig = context.bot_data["config"]
    state_manager: StateManager = context.bot_data["state_manager"]
    observer = start_watching(str(config.mc.full_log_path), state_manager)
    context.bot_data["watchdog_observer"] = observer
    context.bot_data["last_chat_id"] = update.effective_chat.id

@user_is_whitelisted
@require_server_running
async def server_stop_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Stops the Minecraft server."""
    msc: MinecraftServerController = context.bot_data["msc"]
    await context.bot.send_message(chat_id=update.effective_chat.id, text="Stopping the server...")

    observer = context.bot_data.get("watchdog_observer")
    if observer:
        stop_watching(observer)
        context.bot_data["watchdog_observer"] = None

    success = await asyncio.to_thread(msc.stop)
    msg = "Server stopped successfully." if success else "Failed to stop the server. Check logs for details."
    await context.bot.send_message(chat_id=update.effective_chat.id, text=msg)

@user_is_whitelisted
@require_server_running
@require_args(1, "Please provide a command to execute\\. Example: `/cmd say Hello World`")
async def server_cmd_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Executes a command on the Minecraft server console."""
    msc: MinecraftServerController = context.bot_data["msc"]
    command_to_run = " ".join(context.args)
    
    escaped_command = escape_markdown(command_to_run, version=2)
    await context.bot.send_message(chat_id=update.effective_chat.id, text=f"Executing: `{escaped_command}`", parse_mode='MarkdownV2')
    
    if await asyncio.to_thread(msc.run_server_command, command_to_run):
        await context.bot.send_message(chat_id=update.effective_chat.id, text="✅ Command executed.")
    else:
        await context.bot.send_message(chat_id=update.effective_chat.id, text="❌ Failed to execute command.")

@user_is_whitelisted
@require_server_running
@require_args(1, "Please provide a player name to kick\\. Example: `/kick Notch`")
async def server_kick_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Kicks a player from the server."""
    msc: MinecraftServerController = context.bot_data["msc"]
    player_name = context.args[0]
    escaped_player_name = escape_markdown(player_name, version=2)
    
    await context.bot.send_message(chat_id=update.effective_chat.id, text=f"Attempting to kick `{escaped_player_name}`\\.\\.\\.", parse_mode='MarkdownV2')
    
    command = f"{ServerCommand.KICK.value} {player_name}"
    response = await asyncio.to_thread(msc.run_server_command, command)
    if response is not False:
        await context.bot.send_message(chat_id=update.effective_chat.id, text=f"✅ Kick command sent for `{escaped_player_name}`\\.\nServer response: `{response}`", parse_mode='MarkdownV2')
    else:
        await context.bot.send_message(chat_id=update.effective_chat.id, text=f"❌ Failed to kick player `{escaped_player_name}`\\.", parse_mode='MarkdownV2')

@user_is_whitelisted
@require_server_running
@require_args(1, "Please provide a player name to op\\. Example: `/op Notch`")
async def server_op_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Gives a player operator status."""
    msc: MinecraftServerController = context.bot_data["msc"]
    player_name = context.args[0]
    escaped_player_name = escape_markdown(player_name, version=2)

    await context.bot.send_message(chat_id=update.effective_chat.id, text=f"Granting operator status to `{escaped_player_name}`\\.\\.\\.", parse_mode='MarkdownV2')

    command = f"{ServerCommand.OP.value} {player_name}"
    response = await asyncio.to_thread(msc.run_server_command, command)
    if response is not False:
        await context.bot.send_message(chat_id=update.effective_chat.id, text=f"✅ OP command sent for `{escaped_player_name}`\\.\nServer response: `{response}`", parse_mode='MarkdownV2')
    else:
        await context.bot.send_message(chat_id=update.effective_chat.id, text=f"❌ Failed to grant operator status to `{escaped_player_name}`\\.", parse_mode='MarkdownV2')

@user_is_whitelisted
async def server_exit_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Stops the bot and the server gracefully."""
    logger.info("Received /exit command. Initiating graceful shutdown.")
    await context.bot.send_message(chat_id=update.effective_chat.id, text="Shutting down the bot and server...")
    
    # This signals run_polling() to stop. The cleanup logic in main.py will handle the rest.
    context.application.stop_running()
