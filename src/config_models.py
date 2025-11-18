from pydantic import (BaseModel,
                      Field,
                      model_validator,
                      field_validator)

from pathlib import Path
import logging
logger = logging.getLogger(__name__)

class ServerConfig(BaseModel):
    """Holds the data of the config.toml."""
    dir: str
    jar: str
    min_gb: int = Field(..., ge=1, le=12)  #
    max_gb: int = Field(..., ge=1, le=12)
    screen_name: str

    @model_validator(mode="after")
    def ensure_order(self):
        if self.min_gb > self.max_gb:
            self.min_gb, self.max_gb = self.max_gb, self.min_gb
            logger.warning(f"ALERT: 'min_gb' > 'max_gb', check your 'config.toml'! Auto-correcting the order...")
        return self

    @field_validator("jar")
    @classmethod
    def validate_jar(cls, v: str) -> str:
        if not v.lower().endswith(".jar") or len(v) < 5:
            raise ValueError("'jar' must end with .jar! Check your 'config.toml'!")
        return v

    @field_validator("dir")
    @classmethod
    def check_dir_exists(cls, v: str) -> str:
        p = Path(v)
        if p.exists():
            return v
        else:
            raise ValueError(f"{v} Could not be found! Check your 'config.toml' and make sure to enter an existing directory.")

    @property
    def java_command(self) -> list[str]:
        return [
            "java",
            f"-Xms{self.min_gb}G",
            f"-Xmx{self.max_gb}G",
            "-jar",
            self.jar
        ]

    def __str__(self) -> str:
        return f"java -Xms{self.min_gb}G -Xmx{self.max_gb}G -jar {self.jar}"

if __name__ == "__main__":
    # A quick Test
    print(">> Testing config_models.py")
    ServerConfig(max_gb=4,
                min_gb="k", # Test
                dir="C:/Users",
                jar="paper.jar",
                screen_name="Lustiger Screen")
