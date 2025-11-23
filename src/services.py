import subprocess
import logging
from mcrcon import MCRcon, MCRconException

from .config_models import ServerConfig
from .terminal_service import run_commands, get_all_running_screens
from .server_commands import ServerCommand

logger = logging.getLogger(__name__)

class MinecraftServerController:
    def __init__(self, server_config: ServerConfig):
        self.config = server_config
        self.rcon = MCRcon(
            host=self.config.rcon_host,
            port=self.config.rcon_port,
            password=self.config.rcon_password
        )

    def _compose_server_start_command(self) -> list:
        """Returns a list of the start command arguments for a server."""
        return ["screen", "-dmS", self.config.screen_name, *self.config.java_command]

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

    def start(self):
        """Starts the Minecraft Server in a screen session."""
        if self.screen_name in get_all_running_screens():
            logger.warning(f"A screen session named '{self.screen_name}' is already running. "
                           f"Assuming server is already starting or running.")
            return
            
        server_start_command = self._compose_server_start_command()
        logger.info(">> Launching the server...")
        try:
            run_commands(server_start_command, self.config.dir)
            logger.info(f"Server process started in screen session '{self.screen_name}'.")
        except (subprocess.CalledProcessError, FileNotFoundError) as e:
            logger.exception("Could not start the server! Check your 'config.toml' and ensure 'screen' is installed.")
            raise e

    def stop(self) -> bool:
        """Stops the Minecraft server using an RCON command."""
        logger.info(">> Sending stop command to the server via RCON...")
        return self.run_server_command(ServerCommand.STOP.value)

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
