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
        
    def start(self):
        """Starts the Minecraft Server"""
        server_start_command = self._compose_server_start_command()
        logger.info(">> Launching the server...")
        #logger.info(f"- server_start_command = {" ".join(server_start_command)}")
        try:
            run_commands(server_start_command, self.config.dir)
        except Exception as e:
            logger.exception("Could not Start the server! Check your 'config.toml' values?")
            raise e
        logger.info("Server is running...")

    def stop(self):
        """Stops the Minecraft server"""
        logger.info(">> Stopping the server...")
        try:
            stop_cmd = ["screen", "-S", self.config.screen_name, "-X", "stuff","stop\n"]
            logger.debug("Right not 'stop_cmd' has written 'stop\ n' (ignore the space btw \ and n)")
            run_commands(stop_cmd) # target directory is not needed here
            logger.info("Server stopped!")
        except subprocess.CalledProcessError as e:
            logger.exception("Could not stop the server!")

    

if __name__ == "__main__":


    config = load_config()

    server_controller = MinecraftServerController(config)
    server_controller.stop()