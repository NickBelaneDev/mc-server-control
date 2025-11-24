import logging
from mcrcon import MCRcon, MCRconException
from enum import Enum, auto

from src.config_models import ServerConfig
from .server_commands import ServerCommand
from .terminal_service import ScreenProcessService


class ServerStatus(Enum):
    STOPPED = auto()
    RUNNING = auto()
    STARTING = auto()
    CRASHED = auto()

logger = logging.getLogger(__name__)

class MinecraftServerController:
    def __init__(self, server_config: ServerConfig):
        self.config = server_config
        self.rcon = MCRcon(
            host=self.config.rcon_host,
            port=self.config.rcon_port,
            password=self.config.rcon_password
        )
        self.process_service = ScreenProcessService(
            working_dir=self.config.dir,
            screen_name=self.config.screen_name
        )

    @property
    def screen_name(self) -> str:
        return self.config.screen_name

    @property
    def is_running(self) -> bool:
        """
        Checks if the server is running by attempting an RCON connection.
        This is more reliable than checking for a screen session.
        """
        try:
            self.rcon.connect()
            self.rcon.disconnect()
            return True
        except MCRconException:
            return False
        except ConnectionRefusedError: # Also catch if the port is not even open
            return False

    def get_server_status(self) -> ServerStatus:
        """
        Provides a comprehensive status of the server.

        Returns:
            ServerStatus: The current status (STOPPED, RUNNING, STARTING, CRASHED).
        """
        process_running = self.process_service.is_process_running()
        rcon_responsive = self.is_running

        if process_running and rcon_responsive:
            return ServerStatus.RUNNING
        elif process_running and not rcon_responsive:
            return ServerStatus.STARTING
        elif not process_running and self.process_service.get_pid() is not None:
            return ServerStatus.CRASHED
        else: # not process_running and no pid file
            return ServerStatus.STOPPED

    def start(self):
        """Starts the Minecraft Server in a screen session."""
        if self.process_service.is_process_running():
            logger.warning(f"Server process is already running with PID {self.process_service.get_pid()}. "
                           f"Assuming server is already started.")
            return

        # Clean up old PID file if it exists and the process is dead
        self.process_service.remove_pid_file()

        self.process_service.start_process(self.config.java_command)

    def stop(self) -> bool:
        """Stops the Minecraft server using an RCON command."""
        logger.info(">> Sending stop command to the server via RCON...")
        response = self.run_server_command(ServerCommand.STOP.value)
        self.process_service.remove_pid_file() # Clean up PID file after stopping
        return bool(response)

    def run_server_command(self, command: str) -> bool | str:
        """Runs a command on the Minecraft server via RCON."""
        if not isinstance(command, str):
            logger.error("Invalid command type. Command must be a string.")
            return False
        
        try:
            self.rcon.connect()
            response = self.rcon.command(command)
            logger.info(f"Command '{command.strip()}' executed via RCON. Response: {response}")
            self.rcon.disconnect()
            return response
        except MCRconException as e:
            logger.error(f"Failed to execute RCON command '{command.strip()}': {e}")
            return False
        except ConnectionRefusedError:
            logger.error(f"RCON connection refused. Is the server running and is RCON configured correctly?")
            return False
