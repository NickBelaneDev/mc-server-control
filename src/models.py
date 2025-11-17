from pydantic import BaseModel

class CommandsModel(BaseModel):
    commands: list[str]

class TargetModel(BaseModel):
    dir: str

class RunCommand(BaseModel):
    commands_model: CommandsModel