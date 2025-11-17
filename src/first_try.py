import subprocess
from pydantic import BaseModel
print("--- Python-Skript startet ---\n")

# Wir definieren den Befehl, den wir ausführen wollen.
# WICHTIG: Wir übergeben ihn als Liste von Strings.

class RunCommand(BaseModel):
    pass

def _run(command: list[str], target: str):

    # Führe den Befehl aus UND fange die Ausgabe in der 'result'-Variable
    result = subprocess.run(command,
                            capture_output=True,
                            text=True,
                            cwd=target)

    # Jetzt gehört die Ausgabe uns!
    print("--- Python hat die Ausgabe gefangen ---")
    print("Das ist der Standard-Output (stdout):")
    print(result.stdout)

    # Wir können auch nach Fehlern schauen (stderr)
    print("Das ist der Standard-Fehler (stderr):")
    print(result.stderr)

    print("--- Python-Skript beendet ---")

_run(["ls", "-l"], "/mc/server-1-21-10")