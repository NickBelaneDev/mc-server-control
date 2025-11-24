Fehlerquellen & Stabilitätsprobleme
A. Abhängigkeit von screen Parsing
In src/terminal_service.py parst du den Output von screen -ls mittels String-Manipulation (split), um zu prüfen, ob der Server läuft.

Das Problem: Das Parsing ist fragil. Wenn sich die Output-Formatierung von screen je nach Linux-Distro oder Version ändert, 
oder wenn ein anderer Screen-Prozess einen ähnlichen Namen hat, schlägt die Erkennung fehl (is_running gibt falsche Werte 
für den Server zurück).

Empfehlung: Nutze PID-Files. Wenn du den Server startest, speichere die Prozess-ID (PID). Prüfe dann, ob der Prozess mit dieser ID noch existiert.
