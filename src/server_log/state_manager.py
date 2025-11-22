import re
import threading
from dataclasses import dataclass, field
from datetime import datetime
from typing import List, Optional, Callable, Awaitable, Any
import logging
import asyncio

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
        self.loop = None  # Event loop for scheduling async callbacks

    def set_event_loop(self, loop: asyncio.AbstractEventLoop):
        """Sets the event loop for scheduling async callbacks."""
        self.loop = loop

    def register_ready_callback(self, callback: Callable[[], Awaitable[None]]):
        """Registers an async callback to be called when the server is ready."""
        self._ready_callback = callback

    def get_current_state(self) -> ServerState:
        """Returns a copy of the current server state in a thread-safe manner."""
        with self._lock:
            return ServerState(
                is_ready=self._state.is_ready,
                started_at=self._state.started_at,
                online_players=list(self._state.online_players)
            )

    def update_from_log(self, event_type: str, data: Any):
        """Updates the server state based on a parsed log event."""
        with self._lock:
            if event_type == "server_ready" and not self._state.is_ready:
                self._state.is_ready = True
                self._state.started_at = datetime.now()
                logger.info(f"Server state updated: IS_READY = True, Players = {self._state.online_players}")
                if self._ready_callback and self.loop:
                    asyncio.run_coroutine_threadsafe(self._ready_callback(), self.loop)

            elif event_type == "player_joined":
                player_name = data
                if player_name not in self._state.online_players:
                    self._state.online_players.append(player_name)
                    logger.info(f"Player '{player_name}' joined. Current players: {self._state.online_players}")

            elif event_type == "player_left":
                player_name = data
                if player_name in self._state.online_players:
                    self._state.online_players.remove(player_name)
                    logger.info(f"Player '{player_name}' left. Current players: {self._state.online_players}")
            
            elif event_type == "player_list":
                # This event provides a complete list of players, so we replace the current list.
                player_list = data
                self._state.online_players = player_list
                logger.info(f"Player list updated: {player_list}")
