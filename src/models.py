from pydantic import BaseModel, Field, model_validator, field_validator

class CommandsModel(BaseModel):
    commands: list[str]

class TargetModel(BaseModel):
    dir: str

class RunCommand(BaseModel):
    commands_model: CommandsModel