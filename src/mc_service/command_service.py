import asyncio
import logging
from typing import Union

from pydantic import ValidationError

from .command_models import KickPlayerCommand, OpPlayerCommand, BaseCommandModel
from .services import MinecraftServerController

logger = logging.getLogger(__name__)

class CommandService:
    """
    A service layer that provides type-safe methods to execute Minecraft server commands.
    It acts as an intermediary between the bot handlers and the MinecraftServerController.
    """

    def __init__(self, msc: MinecraftServerController):
        self.msc = msc

    async def _execute_command(self, command_model: BaseCommandModel) -> Union[str, bool]:
        """
        Validates and asynchronously runs a command model using the MinecraftServerController.
        """
        try:
            command_str = command_model.to_command_string()
            logger.info(f"Executing command: {command_str}")
            return await asyncio.to_thread(self.msc.run_server_command, command_str)
        except ValidationError as e:
            logger.error(f"Command validation failed: {e}")
            return False
        except Exception as e:
            logger.exception(f"An unexpected error occurred during command execution: {e}")
            return False

    async def kick_player(self, player_name: str) -> Union[str, bool]:
        """Builds and executes the 'kick' command."""
        try:
            command_model = KickPlayerCommand(player_name=player_name)
            return await self._execute_command(command_model)
        except ValidationError as e:
            logger.error(f"Kick command validation failed for player '{player_name}': {e}")
            return False

    async def op_player(self, player_name: str) -> Union[str, bool]:
        """Builds and executes the 'op' command."""
        try:
            command_model = OpPlayerCommand(player_name=player_name)
            return await self._execute_command(command_model)
        except ValidationError as e:
            logger.error(f"Op command validation failed for player '{player_name}': {e}")
            return False