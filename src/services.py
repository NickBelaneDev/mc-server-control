import subprocess

from .config_loader import load_config
from .config_models import ServerConfig
import logging
logger = logging.getLogger(__name__)
from .terminal_service import run_commands, get_all_running_screens

class MinecraftServerController:
    def __init__(self, server_config: ServerConfig):
        self.config = server_config

    def _compose_server_start_command(self) -> list:
        """Returns a String of the start command for a server."""
        return ["screen",
                "-dmS", self.config.screen_name,
                *self.config.java_command]

    @property
    def screen_name(self) -> str:
        return self.config.screen_name

    @property
    def is_running(self) -> bool:
        """Checks if a screen session with the configured name is currently running."""
        return self.config.screen_name in get_all_running_screens()

    @property
    def java_command(self) -> list:
        return self.config.java_command

    def start(self):
        """Starts the Minecraft Server"""
        server_start_command = self._compose_server_start_command()
        logger.info(">> Launching the server...")
        #logger.info(f"- server_start_command = {" ".join(server_start_command)}")
        try:
            run_commands(server_start_command, self.config.dir)
            logger.info("Server is running...")
        except (subprocess.CalledProcessError, FileNotFoundError) as e:
            logger.exception("Could not start the server! Check your 'config.toml' values and ensure 'screen' is installed.")
            raise e

    def stop(self) -> bool:
        """Stops the Minecraft server and returns True on success, False on failure."""
        logger.info(">> Stopping the server...")
        # Later on we will create Enum classes for this
        return self.run_server_command("stop")

    def run_server_command(self, command: str) -> bool:
        """Run a minecraft server command through the console."""
        if not isinstance(command, str):
            raise TypeError("Command must be a string.")
        
        if not command.endswith("\n"):
            command += "\n"
        
        try:
            _cmd = ["screen", "-S", self.config.screen_name, "-X", "stuff", command]
            run_commands(_cmd)
            logger.info(f"Command '{command.strip()}' executed successfully.")
        except subprocess.CalledProcessError:
            logger.error(f"Failed to run server command: {command.strip()}. Is the screen session running?")
            return False
        return True

    def kick_player(self, player: str) -> bool:
        """Kicks a player from the server. Returns True on success."""
        command = f"kick {player}"
        if self.run_server_command(command):
            logger.info(f"Player '{player}' kicked successfully.")
            return True
        else:
            logger.error(f"Failed to kick player: {player}")
            return False

    def op_player(self, player: str) -> bool:
        """Gives a player operator status. Returns True on success."""
        command = f"op {player}"
        if self.run_server_command(command):
            logger.info(f"Player '{player}' is now an Operator.")
            return True
        else:
            logger.error(f"Failed to op player: {player}")
            return False


if __name__ == "__main__":
    config = load_config()

    server_controller = MinecraftServerController(config)
    server_controller.stop()