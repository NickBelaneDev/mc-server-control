import subprocess

from .config_loader import load_config
from .config_models import ServerConfig
import logging
logger = logging.getLogger(__name__)


def _run(commands: list[str], target=None) -> str|None:
    try:
        if target:
            result = subprocess.run(commands,
                                    capture_output=True,
                                    text=True,
                                    cwd=target,
                                    check=True)

        else:
            result = subprocess.run(commands,
                                    capture_output=True,
                                    text=True,
                                    check=True)

        return result.stdout

    except subprocess.CalledProcessError as e:
        logger.exception("Could not run the subprocess command.")
        logger.error(f"Command: {e.cmd}")
        logger.error(f"Returncode: {e.returncode}")
        logger.error(f"stdout: {e.stdout}")
        logger.error(f"stderr: {e.stderr}")
        raise e

    except FileNotFoundError as e:
        logger.exception(f"Could not find the correct file {commands[-1]}.")
        raise e

class MinecraftServerController:
    def __init__(self, server_config: ServerConfig):
        self.target = server_config.dir
        self.min_gb = server_config.min_gb
        self.max_gb = server_config.max_gb
        self.jar = server_config.jar
        self.java_command = server_config.java_command
        self.screen_name = server_config.screen_name

    def _compose_server_start_command(self) -> list:
        """Returns a String of the start command for a server."""
        return ["screen",
                "-dmS", self.screen_name,
                *self.java_command]

    def start(self):
        """Starts the Minecraft Server"""
        server_start_command = self._compose_server_start_command()
        logger.info(">> Launching the server...")
        #logger.info(f"- server_start_command = {" ".join(server_start_command)}")
        try:
            _run(server_start_command, self.target)
        except Exception as e:
            logger.exception("Could not Start the server! Check your 'config.toml' values?")
            raise e
        logger.info("Server is running...")

    def stop(self):
        """Stops the Minecraft server"""
        logger.info(">> Stopping the server...")
        try:
            stop_cmd = ["screen", "-S", self.screen_name, "-X", "stuff","stop"]
            logger.debug("Right not 'stop_cmd' has written 'stop\ n' (ignore the space btw \ and n)")
            _run(stop_cmd, self.target)
            logger.info("Server stopped!")
        except subprocess.CalledProcessError as e:
            logger.exception("Could not stop the server!")



if __name__ == "__main__":


    config = load_config()

    server_controller = MinecraftServerController(config)
    server_controller.stop()