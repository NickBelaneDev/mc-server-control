import logging
from datetime import datetime
from typing import Optional

from pydantic import BaseModel, Field

from .parser import LogPattern

logger = logging.getLogger(__name__)


class ServerState(BaseModel):
    """Pydantic model representing the server's current state."""
    is_ready: bool = False
    online_players: list[str] = Field(default_factory=list)
    player_uuids: dict[str, str] = Field(default_factory=dict)
    last_error: Optional[str] = None
    started_at: Optional[datetime] = None


class StateManager:
    """Manages the server state based on log events."""

    def __init__(self):
        self.state = ServerState()
        logger.info("StateManager initialized with default state.")

    def update_from_log(self, pattern: LogPattern, data: dict):
        """Updates the state based on a parsed log event."""
        logger.debug(f"Updating state with event: {pattern.name}, data: {data}")

        if pattern == LogPattern.SERVER_DONE:
            self.state.is_ready = True
            self.state.started_at = datetime.now()
            logger.info("Server is ready!")

        elif pattern == LogPattern.USER_LOGIN:
            username = data.get("username")
            if username and username not in self.state.online_players:
                self.state.online_players.append(username)
                logger.info(f"Player '{username}' added to online list.")

        elif pattern in (LogPattern.USER_LOGOUT, LogPattern.PLAYER_DISCONNECTED):
            username = data.get("username")
            if username and username in self.state.online_players:
                self.state.online_players.remove(username)
                logger.info(f"Player '{username}' removed from online list.")

        elif pattern == LogPattern.PLAYER_UUID:
            username = data.get("username")
            uuid = data.get("uuid")
            if username and uuid:
                self.state.player_uuids[username] = uuid
                logger.info(f"Stored UUID for player '{username}'.")

        elif pattern == LogPattern.SERVER_ERROR:
            error_message = data.get("error_message")
            self.state.last_error = error_message
            logger.error(f"Server error detected: {error_message}")

        elif pattern == LogPattern.LIST_PLAYERS:
            # This is the "Active Sync" from your plan.md
            # It overwrites the current player list with the ground truth from the server.
            player_str = data.get("players", "")
            if player_str:
                # Split by comma and strip whitespace from each name
                current_players = {p.strip() for p in player_str.split(',') if p.strip()}
            else:
                current_players = set()

            self.state.online_players = sorted(list(current_players))
            logger.info(f"Player list synced via /list. Online: {self.state.online_players}")

    def get_current_state(self) -> ServerState:
        """Returns the current state model."""
        return self.state
