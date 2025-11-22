
# Minecraft Server Telegram Controller

A Python-based Telegram bot to manage your self-hosted Minecraft server. It allows you to start, stop, and monitor your server remotely, making it perfect for servers running on headless systems like a Proxmox LXC container or any Linux server.

 <!-- It's a good idea to add a small GIF showing the bot in action! -->

## ✨ Features

- **Remote Control:** Start and stop your Minecraft server from anywhere using simple Telegram commands.
- **Live Status:** Get real-time server status, including online status, player count, and a list of online players.
- **Log Monitoring:** Actively watches the `latest.log` file to determine server state (e.g., starting up, ready) and track player joins/leaves.
- **Graceful Shutdown:** Ensures the server and the bot shut down cleanly on exit.
- **Easy Configuration:** All settings are managed in a simple `config.toml` file.
- **Background Operation:** Uses `screen` to run the Minecraft server process reliably in the background.

## ⚙️ How It Works

The project consists of three main components that work together:

1.  **`MinecraftServerController`**: A service that interacts with the system shell to start (`screen -dmS ...`) and stop (`screen -X stuff "stop\n"`) the Minecraft server.
2.  **Log Watcher & Parser**: A `watchdog` process monitors `logs/latest.log` for changes. When new lines are added, a parser uses regex to identify key events (server ready, player login/logout, errors).
3.  **`StateManager`**: This component acts as the "single source of truth." It maintains the current state of the server (e.g., `is_ready`, `online_players`) based on events from the Log Watcher.
4.  **Telegram Bot**: Provides a user-friendly command interface. It communicates with the `MinecraftServerController` to manage the server and queries the `StateManager` to report the server's status.

This architecture ensures that the status information is based on the server's actual log output, not just whether the `screen` process exists.

## 📋 Prerequisites

Before you begin, ensure you have the following installed on your server:

- A Linux-based system (the use of `screen` makes it ideal for Linux).
- Python 3.10+
- Java (the version required by your Minecraft server `.jar` file).
- The `screen` utility: `sudo apt-get update && sudo apt-get install screen`
- A working Minecraft server installation.

## 🚀 Setup & Installation

1.  **Clone the Repository**
    ```bash
    git clone <your-repository-url>
    cd minecraft-server
    ```

2.  **Create a Virtual Environment and Install Dependencies**
    It's highly recommended to use a virtual environment.
    ```bash
    python -m venv .venv
    source .venv/bin/activate  # On Windows use `.venv\Scripts\activate`
    pip install -r requirements.txt
    ```

3.  **Create your Environment File**
    You'll need a Telegram Bot Token. Talk to the [BotFather](https://t.me/BotFather) on Telegram to create a new bot and get your token.

    Copy the template and add your token:
    ```bash
    cp empty.env .env
    ```
    Now, edit `.env` and paste your token:
    ```
    BOT_TOKEN='123456:ABC-DEF1234ghIkl-zyx57W2v1u123ew11'
    ```

4.  **Configure Your Server**
    Open `config.toml` and fill in the details for your Minecraft server. **This is the most important step!**
    ```toml
    # ---------- Minecraft Server Configuration -------------
    [mc]
    # IMPORTANT: Use the full, absolute path to your server directory
    dir = "/home/user/minecraft/my_server"
    jar = "paper-1.21-10.jar" # The server .jar file
    min_gb = 4 # Minimum RAM
    max_gb = 4 # Maximum RAM
    screen_name = "minecraft_server" # A unique name for the screen session
    log_file = "logs/latest.log" # Relative path from the server directory
    ```

## ▶️ Running the Bot

Once everything is configured, you can start the bot:
```bash
python main.py
```
The bot will start, and you can now interact with it on Telegram! To stop the bot and the server, you can either use the `/exit` command or press `Ctrl+C` in the terminal.

## 🤖 Telegram Commands

- `/start` - Starts the Minecraft server if it's not already running.
- `/stop` - Sends the `stop` command to the server for a graceful shutdown.
- `/status` - Provides a detailed status of the server, including online status, player count, and a list of online players.
- `/help` - Shows a list of available commands.
- `/exit` - Shuts down the Minecraft server and the bot gracefully.
