import subprocess

print("--- Python-Skript startet ---")

# Wir definieren den Befehl, den wir ausführen wollen.
# WICHTIG: Wir übergeben ihn als Liste von Strings.
befehl = ["ls"]

subprocess.run(befehl)
print("--- Python-Skript beendet ---\n")