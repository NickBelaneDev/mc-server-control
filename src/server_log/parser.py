import re
from enum import Enum
from typing import Optional, Tuple


class LogPattern(Enum):
    """Enumeration of regex patterns for parsing Minecraft log lines."""
    USER_LOGIN = re.compile(r": (?P<username>\w+) joined the game")
    USER_LOGOUT = re.compile(r": (?P<username>\w+) left the game")
    PLAYER_DISCONNECTED = re.compile(r": (?P<username>\w+) lost connection: (?P<reason>.*)")
    SERVER_DONE = re.compile(r"Done \([\d.]+s\)! For help, type \"help\"") # Server finished loading
    USER_COMMAND = re.compile(r": (?P<username>\w+) issued server command: (?P<command>.*)")
    PLAYER_UUID = re.compile(r"UUID of player (?P<username>\w+) is (?P<uuid>[\w-]+)")
    PLAYER_CHAT = re.compile(r"<(?P<username>\w+)> (?P<message>.*)")

    # Catches severe errors and exceptions from the server log
    SERVER_ERROR = re.compile(r"^(?:\[[^\]]+\])? \[(?:[^\]]+)\] \[(?:ERROR|SEVERE)\]: (?!\[Trident\])(?P<error_message>.*)", re.MULTILINE)

    # Parses the output of the /list command. The space after the colon is optional.
    LIST_PLAYERS = re.compile(r"There are (?P<online>\d+) of a max of (?P<max>\d+) players online: ?(?P<players>.*)")


class LogParser:
    """Parses Minecraft log lines to extract meaningful events."""

    @staticmethod
    def parse_line(line: str) -> Optional[Tuple[LogPattern, dict]]:
        """
        Parses a single log line against all known patterns.

        Args:
            line: The log line string.

        Returns:
            A tuple containing the matched LogPattern and a dictionary
            of the extracted data (from named groups), or None if no pattern matched.
        """
        for pattern_enum in LogPattern:
            match = pattern_enum.value.search(line)
            if match:
                return pattern_enum, match.groupdict()
        return None

if __name__ == "__main__":
    # --- Test cases to demonstrate the parser's functionality ---
    print(">> Testing LogParser...")

    test_lines = [
        "[12:59:33] [Server thread/INFO]: RebellTank joined the game",
        "[13:05:34] [Server thread/INFO]: RebellTank left the game",
        "[12:56:44] [Server thread/INFO]: Done (22.664s)! For help, type \"help\"",
        "[14:53:51 INFO]: RebellTank issued server command: /gamemode creative",
        "[13:05:34] [Server thread/INFO]: SomeUser lost connection: Disconnected",
        "[12:59:31] [User Authenticator #0/INFO]: UUID of player RebellTank is de3b7906-f31a-48f7-9bf4-84d477003cb2",
        "[13:15:00] [Server thread/INFO]: <RebellTank> Hello World!",
        "[main/ERROR]: Failed to load properties from file: server.properties",
        "[12:59:47] [Server thread/INFO]: There are 2 of a max of 20 players online: RebellTank, Steve",
        "[12:57:26] [Server thread/INFO]: There are 0 of a max of 20 players online:",
        "[12:56:22] [ServerMain/INFO]: [bootstrap] Loading Paper 1.21.10-108-main@97452e1 (2025-11-10T18:27:52Z) for Minecraft 1.21.10"  # Should not match
    ]

    parser = LogParser()
    for test_line in test_lines:
        result = parser.parse_line(test_line)
        if result:
            pattern_found, data = result
            print(f"\nLine: '{test_line.strip()}'")
            print(f"  -> Matched: {pattern_found.name}")
            print(f"  -> Data: {data}")
        else:
            print(f"\nLine: '{test_line.strip()}'")
            print("  -> No match found.")
