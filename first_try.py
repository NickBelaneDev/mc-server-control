import subprocess

print("--- Python-Skript startet ---\n")

# Wir definieren den Befehl, den wir ausführen wollen.
# WICHTIG: Wir übergeben ihn als Liste von Strings.

def check_pwd():
    befehl = ["pwd"]

    _result = subprocess.run(
        befehl,
        capture_output=True,
        text=True)
    return _result

result = check_pwd()
print(f"{result.stderr=}")
print(f"{result.stdout=}")
print("\n--- Python-Skript beendet ---")