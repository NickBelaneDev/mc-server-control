Das Konzept: Der "Log-Stream-Processor"
Wir bauen eine Pipeline, die parallel zu deinem Telegram-Bot läuft. Sie besteht aus drei Komponenten: Watcher (liest), Parser (versteht) und State (speichert).

## **Die Architektur-Komponenten**

### **A. Der Watchdog (Der "Input")**
**Aufgabe**: Hängt an logs/latest.log (Standard Minecraft Log-Datei).
**Technik**: Nutze watchdog (wie in deiner Frage besprochen) oder einen asyncio-File-Reader.
**Warum**: Es ist extrem ressourcenschonend. Es feuert nur Events, wenn wirklich eine Zeile geschrieben wird. Du musst nicht pollen.
**Trigger**: Startet automatisch, wenn dein msc.start() erfolgreich war.



### **B. Der Parser (Der "Versteher")**
**Aufgabe**: Nimmt die rohe Textzeile und entscheidet: "Müll" oder "Info"?
**Technik**: Hier kommen deine Regex ins Spiel. Aber nicht auf die ganze Datei, sondern nur auf die eine neue Zeile.

**Patterns, die du brauchst:**
LOGIN_PATTERN: Sucht nach "X joined the game" -> Extrahiert Usernamen.
LOGOUT_PATTERN: Sucht nach "X left the game" -> Extrahiert Usernamen.
SERVER_DONE_PATTERN: Sucht nach "Done (...s)!" -> Setzt Server-Status auf "Ready".
ERROR_PATTERN: Sucht nach "Exception" oder "[SEVERE]" -> Feuert Alarm.


#### **C. Der State Manager (Das "Gedächtnis")**
**Aufgabe**: Hält die Wahrheit im RAM (Python Class/Dictionary).
**Struktur**:

Python
`
class ServerState:
    is_online: bool
    online_players: list[str]  # z.B. ["Robert", "Admin"]
    last_error: str
`

**Logik**:
Login-Event kommt -> Füge Namen zu online_players hinzu.
Logout-Event kommt -> Entferne Namen aus online_players.
Lösung deiner spezifischen Anforderungen



## **1. "Wer ist online und welche Rechte haben sie?" (Security Check)**

Der Log sagt dir nur, wer kommt. Er sagt dir nicht, ob derjenige Admin ist.
Der Plan: Du brauchst eine Referenz-Datei (Source of Truth).
Lies beim Start des Bots (oder beim Login-Event) die ops.json (Admins) oder whitelist.json aus dem Server-Ordner.

#### **Der Workflow:**
Regex meldet: "UnbekannterUser123 joined".
Bot checkt ops.json: Ist "UnbekannterUser123" drin? -> Nein.
Bot checkt interne whitelist (falls du eine hast).
Alarm: Wenn unbekannt -> Nachricht an Telegram: "Fremder Login erkannt!". Optional: Sende kick UnbekannterUser123 an die Screen-Session via msc.

## **2. "Läuft der Server?"**
Verlasse dich nicht nur auf screen -ls. Der Screen kann laufen, aber der Java-Prozess darin kann hängen.
Nutze den Watchdog: Wenn seit 5 Minuten kein "Can't keep up" oder irgendein Log kommt, ist der Server evtl. gefroren. (Optionaler Heartbeat).
Wichtiger: Das Log-Pattern "Done!" bestätigt dir den erfolgreichen Start.

## **3. Umgang mit Fehlern (Desync verhindern)**
Das ist dein Punkt "Fehleranfälligkeit". Was passiert, wenn der Server abschmiert, ohne "X left the game" zu schreiben? Dann denkt dein Bot, die Spieler sind noch online.
Die Lösung: Der "Active Sync" (Fallback)
Verlasse dich für Echtzeit-Alarme auf den Log-Stream (schnell).

#### **Implementiere einen Periodic Task (z.B. alle 5 Minuten oder wenn du /status im Bot drückst):**
Der Bot sendet den Befehl list in die Screen-Session (stuff "list\n").
Der Log-Stream fängt die Antwort ab: "There are 2/20 players online: Robert, Peter".
Der Parser erkennt diese spezielle Zeile und überschreibt den Cache hart. Damit korrigierst du eventuelle Fehler automatisch.
Zusammenfassung des Plans
Erweitere `MinecraftServerController`: Füge eine Methode `attach_monitor()` hinzu, die den Watchdog startet.

#### **Erstelle src/log_parser.py:**
**Definiere deine Regex-Patterns.**
Implementiere die Logik: "Wenn Zeile X passt, update State Y".

#### **Erstelle `src/state_manager.py`:**
Eine Klasse (am besten ein Singleton oder eine Instanz in bot_data), die die Listen hält.
Lade hier auch statisch deine ops.json für den Rechte-Check.

#### **Telegram Integration:**

Der Bot liest nur aus dem `StateManager`. Er muss nie direkt Logs parsen.
Damit hast du Performance (Regex nur auf einzelne Zeilen) und Robustheit (durch den Sync-Mechanismus und die Trennung von Logik und Daten).