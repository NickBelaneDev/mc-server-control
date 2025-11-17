import subprocess
from src.config_loader import load_config

config = load_config()

def _compose_server_start_command() -> list:
    """Returns a String of the start command for a server."""
    return ["screen",
            "-dmS", config.screen_name,
            "java",
            *config.java_command]

def _run(commands: list[str], target=config.dir) -> str|None:
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
        print(" --- Command Failed!! ---")
        print(f"Command: {e.cmd}")
        print(f"Returncode: {e.returncode}")
        print(f"stdout: {e.stdout}")
        print(f"stderr: {e.stderr}")
        raise e

    except FileNotFoundError as e:
        print(" --- Command Failed!! ---")
        print(f"Error: FileNotFound {commands[-1]}")
        raise e

class MinecraftServerController:
    def __init__(self):
        self.target = config.dir
        self.min_gb = config.min_gb
        self.max_gb = config.max_gb
        self.jar = config.jar
        self.screen_name = config.screen_name

    def start(self):
        """
        Starts the Minecraft Server
        """
        server_start_command = _compose_server_start_command()
        print(">> Launching the server...")
        print(f"- server_start_command = {server_start_command}")
        try:
            _run(server_start_command, self.target)
        except Exception as e:
            print("Could not Start the server! Check your 'config.toml' values?")
            print(e)
            raise e
        print("Server is running...!")

    def stop(self):
        """Stops the minecraft server"""
        print(">> Stopping the server...")
        _run(["stop"], self.target)
        print("Server stopped!")



if __name__ == "__main__":
    server_controller = MinecraftServerController()
    server_controller.start()