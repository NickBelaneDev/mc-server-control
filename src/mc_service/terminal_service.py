import subprocess
import logging
import os
import psutil
import time

logger = logging.getLogger(__name__)


class ScreenProcessService:
    """Manages a process running inside a detached screen session using a PID file."""

    def __init__(self, working_dir: str, screen_name: str):
        self.working_dir = working_dir
        self.screen_name = screen_name

    @property
    def _pid_file_path(self) -> str:
        """Returns the absolute path to the PID file, named after the screen session."""
        return os.path.join(self.working_dir, f"{self.screen_name}.pid")

    def get_pid(self) -> int | None:
        """Reads the PID from the PID file."""
        try:
            with open(self._pid_file_path, "r") as f:
                return int(f.read().strip())
        except (FileNotFoundError, ValueError):
            return None

    def remove_pid_file(self):
        """Removes the PID file if it exists."""
        if os.path.exists(self._pid_file_path):
            try:
                os.remove(self._pid_file_path)
                logger.debug(f"Removed PID file: {self._pid_file_path}")
            except OSError as e:
                logger.error(f"Error removing PID file: {e}")

    def is_process_running(self) -> bool:
        """Checks if the server process is running based on the PID file."""
        pid = self.get_pid()
        return psutil.pid_exists(pid) if pid else False

    def get_process_uptime(self) -> float:
        """
        Returns the uptime of the managed process in seconds.
        Returns 0.0 if the process is not running or PID is not found.
        """
        pid = self.get_pid()
        if not pid or not psutil.pid_exists(pid):
            return 0.0
        try:
            process = psutil.Process(pid)
            return time.time() - process.create_time()
        except (psutil.NoSuchProcess, psutil.AccessDenied):
            return 0.0

    def start_process(self, command: list[str]):
        """
        Starts the given command in a detached screen session and creates a PID file.
        """
        java_command_str = subprocess.list2cmdline(command)
        # The 'exec' replaces the shell process with the java process.
        # The PID of the java process is written to the PID file.
        shell_command = f"exec {java_command_str} & echo $! > {self.screen_name}.pid"
        screen_command = ["screen", "-dmS", self.screen_name, "sh", "-c", shell_command]

        logger.info(">> Launching the process in a screen session...")
        try:
            # We run the command from the server directory so the PID file is created there.
            subprocess.run(screen_command, check=True, cwd=self.working_dir)
            logger.info(f"Process started in screen session '{self.screen_name}'.")
        except (subprocess.CalledProcessError, FileNotFoundError) as e:
            logger.exception("Could not start the process! Check your config and ensure 'screen' is installed.")
            self.remove_pid_file()  # Clean up on failure
            raise e