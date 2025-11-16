import subprocess

print("--- Python-Skript startet ---")

# Wir definieren den Befehl, den wir ausführen wollen.
# WICHTIG: Wir übergeben ihn als Liste von Strings.
befehl = ["ls", "-l"]

subprocess.run(befehl)
print("--- Python-Skript beendet ---\n")