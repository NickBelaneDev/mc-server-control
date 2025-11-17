import subprocess
from models import CommandModel, RunCommand, TargetModel, StartCommand



def _run(command: list[str], target=None):
    if target:
        result = subprocess.run(command,
                                capture_output=True,
                                text=True,
                                cwd=target)

    else:
        result = subprocess.run(command,
                                capture_output=True,
                                text=True)

    return result

def _start_command(min_gb: int, max_gb: int, file: str) -> str:
    """Returns a String of the start command for a server."""
    start_cmd_mdl = StartCommand(min_gb=min_gb,
                                 max_gb=max_gb,
                                 file_name=file)
    return str(start_cmd_mdl)

def _build_command_model(min_gb: int, max_gb: int, file: str) -> CommandModel:
     return CommandModel(commands=[_start_command(min_gb=min_gb,
                                                    max_gb=max_gb,
                                                    file=file)])


def _build_target_model(target_dir: str) -> TargetModel:
    return TargetModel(dir=target_dir)

def _build_run_command(command_model: CommandModel, targe_model: TargetModel) -> RunCommand:
    return RunCommand(command_model=command_model, target=targe_model)


class MinecraftServerController:
    def __init__(self, folder: str):
        self.target = TargetModel(dir=folder)

    def start(self, min_gb: int, max_gb: int, file: str):
        """

        :param min_gb: Minimum RAM
        :param max_gb: Maximum RAM
        :param file: server file name e.g. 'server.jar' or 'paper.jar'
        :return:
        """
        cmd_mdl = _build_command_model(min_gb=min_gb,
                             max_gb=max_gb,
                             file=file)

        print(cmd_mdl.commands)
        _run(cmd_mdl.commands, self.target.dir)

    def stop(self):
        """Stops the minecraft server"""
        _run(["stop"], self.target.dir)
        raise NotImplementedError

if __name__ == "__main__":
    server_controller = MinecraftServerController("/mc/server-1-21-10")
    server_controller.start(4, 6, "paper.jar")