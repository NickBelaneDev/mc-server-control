from typing import Optional
from pydantic import BaseModel, Field, model_validator, field_validator

class CommandModel(BaseModel):
    commands: list[str]

class TargetModel(BaseModel):
    dir: str

class RunCommand(BaseModel):
    command_model: CommandModel
    target: Optional[TargetModel]


class StartCommand(BaseModel):
    min_gb: int = Field(..., ge=1, le=12) #
    max_gb: int = Field(..., ge=1, le=12)
    file_name: str

    @model_validator(mode="after")
    def ensure_order(self):
        if self.min_gb > self.max_gb:
            self.min_gb, self.max_gb = self.max_gb, self.min_gb
        return self

    @field_validator("file_name")
    def validate_jar(cls, v: str) -> str:
        if not v.lower().endswith(".jar") or len(v) < 5:
            raise ValueError("file_name must end with .jar")
        return v

    def __str__(self):
        return f"java -Xms{self.min_gb}G -Xmx{self.max_gb}G -jar {self.file_name}"

s_c = StartCommand(max_gb=4,
                   min_gb=7,
                   file_name="lkk.jar")
print(str(s_c))