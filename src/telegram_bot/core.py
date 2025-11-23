import asyncio
import logging

from telegram.ext import Application, CommandHandler

from src.mc_service.command_service import CommandService
from ..config_models import AppConfig
from src.mc_service.services import MinecraftServerController
from ..server_log.state_manager import StateManager
from . import handlers

logger = logging.getLogger(__name__)

class TelegramBot:
    def __init__(self, token: str, msc: MinecraftServerController, state_manager: StateManager, config: AppConfig):
        self.msc = msc
        self.state_manager = state_manager
        self.config = config
        self.application = (
            Application.builder()
            .token(token)
            .post_init(self._post_init)
            .build()
        )
        
        self._setup_bot_data()
        self._add_handlers()
        # _register_callbacks() is now called from _post_init

    def _setup_bot_data(self):
        """Stores shared components in bot_data for easy access in handlers."""
        self.application.bot_data["msc"] = self.msc
        self.application.bot_data["state_manager"] = self.state_manager
        self.application.bot_data["config"] = self.config
        self.application.bot_data["command_service"] = CommandService(self.msc)
        self.application.bot_data["watchdog_observer"] = None  # To hold the log watcher instance
        self.application.bot_data["last_chat_id"] = None  # To notify the user who started the server

    def _add_handlers(self):
        """Creates and registers all command handlers for the bot."""
        handler_definitions = {
            "start": handlers.server_start_command,
            "stop": handlers.server_stop_command,
            "status": handlers.server_status_command,
            "help": handlers.help_command,
            "cmd": handlers.server_cmd_command,
            "kick": handlers.server_kick_command,
            "op": handlers.server_op_command,
            "exit": handlers.server_exit_command,
        }
        
        for command, handler_func in handler_definitions.items():
            self.application.add_handler(CommandHandler(command, handler_func))
        
        logger.info("All command handlers have been registered.")

    def _register_callbacks(self, loop: asyncio.AbstractEventLoop):
        """Registers callbacks for server events, like the 'ready' signal."""
        self.state_manager.register_ready_callback(self.on_server_ready)
        # Pass the event loop to the state manager for safe async callbacks
        self.state_manager.set_event_loop(loop)
        logger.info("Server-ready callback and event loop have been registered with the StateManager.")

    async def on_server_ready(self):
        """Async callback triggered by StateManager when the server is ready."""
        chat_id_to_notify = self.application.bot_data.get("last_chat_id")
        if chat_id_to_notify:
            logger.info(f"Server is ready. Notifying chat_id: {chat_id_to_notify}")
            try:
                await self.application.bot.send_message(
                    chat_id=chat_id_to_notify,
                    text="🚀 Server is now ready and accepting players!"
                )
            except Exception as e:
                logger.error(f"Failed to send 'server ready' notification: {e}")

    async def initial_state_sync(self):
        """
        Checks server status on bot start and syncs state if necessary.
        This is useful if the bot is restarted while the server is already running.
        """
        if self.msc.is_running:
            logger.info("Server is already running on bot startup. Starting log watcher and syncing state.")
            # Start watching logs for live updates
            observer = handlers.start_watching(str(self.config.mc.full_log_path), self.state_manager)
            self.application.bot_data["watchdog_observer"] = observer

            # Request player list to get an initial state
            # Use a small delay to ensure RCON is ready
            await asyncio.sleep(2)
            await asyncio.to_thread(self.msc.run_server_command, "list")

    async def _post_init(self, app: Application) -> None:
        """Post-initialization hook to set up async components."""
        loop = asyncio.get_running_loop()
        self._register_callbacks(loop)
        logger.info("Async components initialized via post_init.")
