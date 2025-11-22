import subprocess

import logging
logger = logging.getLogger(__name__)

def run_commands(commands: list[str], target=None) -> str | None:
    try:
        result = subprocess.run(commands,
                                capture_output=True,
                                text=True,
                                cwd=target,  # cwd can be None, which is the default
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
def get_all_running_screens() -> list[str]:
    """
    Gets a list of all currently running screen sessions.
    Returns an empty list if no screens are running or if 'screen' is not installed.
    """
    try:
        # Execute 'screen -ls'. A non-zero exit code is expected if no screens exist.
        result = subprocess.run(["screen", "-ls"], capture_output=True, text=True)

        running_screens = []
        # The output format is typically like "\t<pid>.<screen_name>\t(State)"
        for line in result.stdout.splitlines():
            if "\t" in line and "." in line:
                # Extract "minecraft_server" from "2633.minecraft_server (Detached)"
                parts = line.strip().split("\t")[0]
                screen_name = parts.split(".", 1)[-1]
                running_screens.append(screen_name)
        return running_screens
    except FileNotFoundError:
        logger.error("The 'screen' command was not found. Is it installed on the system?")
        return []