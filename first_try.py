import subprocess

print("--- Python-Skript startet ---\n")

# Wir definieren den Befehl, den wir ausführen wollen.
# WICHTIG: Wir übergeben ihn als Liste von Strings.

def check_pwd() -> str:
    befehl = ["pwd"]
    result = subprocess.run(
        befehl,
        capture_output=True,
        text=True)
    return result.stdout

print(check_pwd())
print("--- Python-Skript beendet ---\n")