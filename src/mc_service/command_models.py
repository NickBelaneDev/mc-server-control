from pydantic import BaseModel, Field

from .server_commands import ServerCommand


class BaseCommandModel(BaseModel):
    """
    Abstract base model for a server command.
    Provides a method to convert the model into a command string.
    """

    def to_command_string(self) -> str:
        """Converts the command model into its string representation."""
        raise NotImplementedError("This method must be implemented by subclasses.")


class KickPlayerCommand(BaseCommandModel):
    """Model for the 'kick' command."""
    player_name: str = Field(..., min_length=1)

    def to_command_string(self) -> str:
        """Returns the formatted kick command string."""
        return f"{ServerCommand.KICK.value} {self.player_name}"


class OpPlayerCommand(BaseCommandModel):
    """Model for the 'op' command."""
    player_name: str = Field(..., min_length=1)

    def to_command_string(self) -> str:
        """Returns the formatted op command string."""
        return f"{ServerCommand.OP.value} {self.player_name}"