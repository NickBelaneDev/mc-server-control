import os
import time
import logging
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler

from .parser import LogParser
from .state_manager import StateManager

logger = logging.getLogger(__name__)

class LogFileHandler(FileSystemEventHandler):
    """Handles file system events for the log file."""

    def __init__(self, file_path: str, state_manager: StateManager):
        self.file_path = os.path.abspath(file_path)
        self.parser = LogParser()
        self.state_manager = state_manager
        # Start reading from the end of the file
        try:
            self.last_pos = os.path.getsize(self.file_path)
        except FileNotFoundError:
            self.last_pos = 0

    def on_created(self, event):
        """
        Called when a file or directory is created.
        This handles cases where the log file is recreated (e.g., on server start).
        """
        if event.src_path == self.file_path:
            logger.info(f"Log file '{os.path.basename(self.file_path)}' was created. Resetting position.")
            self.last_pos = 0
            self._process_new_lines()

    def on_modified(self, event):
        """
        Called when a file or directory is modified.
        """
        if event.src_path == self.file_path:
            self._process_new_lines()
        # Note: We don't need on_moved, as watchdog reports it as on_deleted for the old path
        # and on_created for the new path. on_created is sufficient.

    def _process_new_lines(self):
        """Reads and processes new lines from the log file."""
        try:
            with open(self.file_path, 'r', encoding='utf-8') as f:
                f.seek(self.last_pos)
                new_lines = f.readlines()
                if not new_lines:
                    return

                logger.info(f"Detected {len(new_lines)} new lines in {os.path.basename(self.file_path)}.")
                for line in new_lines:
                    line = line.strip()
                    if not line:
                        continue

                    result = self.parser.parse_line(line)
                    if result:
                        pattern_found, data = result
                        # Pass the event to the state manager
                        self.state_manager.update_from_log(pattern_found, data)

                self.last_pos = f.tell()
        except Exception as e:
            logger.exception(f"Error processing log file: {e}")


def start_watching(log_file: str, state_manager: StateManager):
    """
    Creates and starts the watchdog observer to monitor the log file.
    Returns the observer instance so it can be managed externally.
    """
    watch_dir = os.path.dirname(log_file)
    event_handler = LogFileHandler(log_file, state_manager)
    observer = Observer()
    observer.schedule(event_handler, watch_dir, recursive=False)

    logger.info(f"Starting watchdog for {log_file}")
    observer.start()
    return observer

def stop_watching(observer: Observer):
    """Stops the given watchdog observer."""
    if observer and observer.is_alive():
        logger.info("Stopping watchdog...")
        observer.stop()
        observer.join() # Wait for the thread to finish
        logger.info("Watchdog stopped.")


if __name__ == "__main__":
    # The script assumes 'latest.log' is in the same directory.
    # This is for standalone testing only.
    script_dir = os.path.dirname(__file__)
    log_path = os.path.join(script_dir, 'latest.log')

    # Ensure the log file exists for the test to run
    if not os.path.exists(log_path):
        open(log_path, 'a').close()

    sm = StateManager()
    obs = start_watching(log_path, sm)
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        stop_watching(obs)
