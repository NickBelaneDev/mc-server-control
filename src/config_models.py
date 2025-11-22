from pydantic import (BaseModel,
                      Field,
                      model_validator,
                      field_validator, ValidationError)

from pathlib import Path
import logging
logger = logging.getLogger(__name__)

class BotConfig(BaseModel):
    """Holds the bot-specific configuration."""
    allowed_chat_ids: list[int] = []

class ServerConfig(BaseModel):
    """Holds the data of the config.toml."""
    dir: str
    jar: str
    min_gb: int = Field(..., ge=1, le=12)  #
    max_gb: int = Field(..., ge=1, le=12)
    screen_name: str
    log_file: str = "logs/latest.log"

    @model_validator(mode="after")
    def ensure_order(self):
        """Ensures that min_gb is not greater than max_gb, swapping them if necessary."""
        if self.min_gb > self.max_gb:
            self.min_gb, self.max_gb = self.max_gb, self.min_gb
            logger.warning(f"ALERT: 'min_gb' > 'max_gb', check your 'config.toml'! Auto-correcting the order...")
        return self

    @field_validator("jar")
    @classmethod
    def validate_jar(cls, v: str) -> str:
        """Validates that the 'jar' field value is a valid .jar file name."""
        if not v.lower().endswith(".jar") or len(v) < 5:
            raise ValueError("'jar' must end with .jar! Check your 'config.toml'!")
        return v

    @field_validator("dir")
    @classmethod
    def check_dir_exists(cls, v: str) -> str:
        """Validates that the directory specified in 'dir' exists."""
        p = Path(v)
        if p.exists():
            return v
        else:
            raise ValueError(f"{v} Could not be found! Check your 'config.toml' and make sure to enter an existing directory.")

    @property
    def full_log_path(self) -> Path:
        """Returns the full, absolute path to the log file."""
        return Path(self.dir) / self.log_file

    @property
    def java_command(self) -> list[str]:
        """Constructs the java command as a list of arguments."""
        return [
            "java",
            f"-Xms{self.min_gb}G",
            f"-Xmx{self.max_gb}G",
            "-jar",
            self.jar
        ]

    def __str__(self) -> str:
        """Returns the string representation of the java command."""
        return f"java -Xms{self.min_gb}G -Xmx{self.max_gb}G -jar {self.jar}"

class AppConfig(BaseModel):
    """The root model for the entire application configuration."""
    mc: ServerConfig = Field(..., alias='mc')
    bot: BotConfig = Field(..., alias='bot')

if __name__ == "__main__":
    # A quick Test
    print(">> Testing config_models.py")
    ServerConfig(max_gb=4,
                min_gb=5, # Test
                dir="C:/Users",
                jar="paper.j",
                screen_name="Lustiger Screen")
