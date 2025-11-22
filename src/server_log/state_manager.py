import re
import threading
from dataclasses import dataclass, field
from datetime import datetime
from typing import List, Optional, Callable, Awaitable
import logging

logger = logging.getLogger(__name__)

@dataclass
class ServerState:
    is_ready: bool = False
    started_at: Optional[datetime] = None
    online_players: List[str] = field(default_factory=list)

class StateManager:
    def __init__(self):
        self._state = ServerState()
        self._lock = threading.Lock()
        self._ready_callback: Optional[Callable[[], Awaitable[None]]] = None

        # Regex patterns to parse log lines
        self.patterns = {
            "player_joined": re.compile(r"INFO\]: (.+?) joined the game"),
            "player_left": re.compile(r"INFO\]: (.+?) left the game"),
            "server_ready": re.compile(r"INFO\]: Done \(.+?\)! For help, type \"help\""),
            "player_list": re.compile(r"INFO\]: There are \d+ of a max of \d+ players online: (.*)")
        }

    def register_ready_callback(self, callback: Callable[[], Awaitable[None]]):
        """Registers an async callback to be called when the server is ready."""
        self._ready_callback = callback

    def get_current_state(self) -> ServerState:
        """Returns a copy of the current server state in a thread-safe manner."""
        with self._lock:
            # Return a copy to prevent modification outside the manager
            return ServerState(
                is_ready=self._state.is_ready,
                started_at=self._state.started_at,
                online_players=list(self._state.online_players)
            )

    async def update_from_log(self, line: str):
        """Parses a log line and updates the server state. Triggers callbacks if necessary."""
        with self._lock:
            # --- Server Ready ---
            if not self._state.is_ready and self.patterns["server_ready"].search(line):
                self._state.is_ready = True
                self._state.started_at = datetime.now()
                logger.info(f"Server state updated: IS_READY = True, Players = {self._state.online_players}")
                # Trigger callback outside the lock to avoid deadlocks
                if self._ready_callback:
                    # Since the callback is async, we need to schedule it.
                    # The calling context (log_watcher) is synchronous, so we can't await it here.
                    # The TelegramBot class will handle the async execution.
                    # For simplicity, we assume the bot's event loop is running.
                    import asyncio
                    asyncio.run_coroutine_threadsafe(self._ready_callback(), asyncio.get_running_loop())
                return

            # --- Player Joined ---
            join_match = self.patterns["player_joined"].search(line)
            if join_match:
                player = join_match.group(1)
                if player not in self._state.online_players:
                    self._state.online_players.append(player)
                    logger.info(f"Player '{player}' joined. Current players: {self._state.online_players}")
                return

            # --- Player Left ---
            left_match = self.patterns["player_left"].search(line)
            if left_match:
                player = left_match.group(1)
                if player in self._state.online_players:
                    self._state.online_players.remove(player)
                    logger.info(f"Player '{player}' left. Current players: {self._state.online_players}")
                return