
# 🤖 Minecraft Server Telegram Controller

A Python bot to manage your Minecraft server via Telegram. Start, stop, and check the status of your server from anywhere. Designed for headless Linux servers and can run as a `systemd` service for maximum reliability.

 <!-- It's a good idea to add a small GIF showing the bot in action! -->

## ✨ Features

-   **🚀 Remote Control:** Start and stop your server with simple commands.
-   **📊 Live Status:** Get real-time status, including server state, uptime, and a live player list.
-   **⚙️ Direct Command Execution:** Run any command on your server console directly from Telegram (e.g., `/cmd whitelist add <player>`).
-   **🛡️ Robust Background Operation:**
    -   Uses `screen` to run the Minecraft server process reliably.
    -   The bot itself can run as a `systemd` service for automatic startup and management.
-   **📝 Easy Configuration:** Simple setup using a `config.toml` file.
-   **🔒 Secure:** Uses a `.env` file for your private bot token.

## 📋 Prerequisites

-   Linux-based OS
-   Python 3.10+
-   Java (for your Minecraft server)
-   `screen` (`sudo apt-get install screen`)
-   An existing Minecraft server installation.

## 🚀 Quick Start

1.  **Clone the repo:**
    ```bash
    git clone https://github.com/NickBelaneDev/mc-server-control
    cd minecraft-server
    ```

2.  **Install dependencies:**
    ```bash
    python -m venv .venv
    source .venv/bin/activate 
    pip install -r requirements.txt
    ```

3.  **Set up your bot:**
    -   Get a token from [BotFather](https://t.me/BotFather) on Telegram.
    -   Copy `empty.env` to `.env` and add your token:
    ```bash
    cp empty.env .env
    ```
    ```ini
    BOT_TOKEN='YOUR_SECRET_TOKEN_HERE'
    ```

4.  **Configure your server:**
    -   Edit `config.toml` with the **absolute path** to your server directory and other settings.
    ```toml
    # ---------- Minecraft Server Configuration -------------
    [mc]
    dir = "/home/user/minecraft/my_server"  # Absolute path to your server directory
    jar = "paper-1.21-10.jar"               # The initial server.jar file
    min_gb = 4                              # Minimum RAM
    max_gb = 4                              # Maximum RAM
    screen_name = "minecraft_server"        # Custom Screen name
    log_file = "logs/latest.log"            # Default log file name
    rcon_host = "localhost"                 # RCON server host
    rcon_port = 25575                       # Your RCON port
    rcon_password = "Your Password"         # Your RCON password

    # ---------- Telegram Bot Configuration -------------
    [bot]
    # A list of Telegram Chat IDs that are allowed to use this bot.
    # Get your ID from a bot like @userinfobot
    allowed_chat_ids = [123456789] # Example
    ```

    -   **Enable RCON on your Minecraft server:**
        In your Minecraft server's `server.properties` file, ensure RCON is enabled and the credentials match your `config.toml`:
        ```properties
        enable-rcon=true
        rcon.port=25575
        rcon.password=Your Password
        ```
        > **Note:** You must restart the Minecraft server for these changes to take effect.

5.  **Run the bot for testing:**
    ```bash
    python main.py
    ```
    The bot will start polling. You can stop it with `Ctrl+C`. For permanent use, see the next section.

## ⚙️ Running as a Service (Recommended for Linux)

Running the bot as a `systemd` service ensures it starts automatically on boot and restarts if it ever crashes.

1.  **Create a service file:**
    Create a new service file for `systemd`:
    ```bash
    sudo nano /etc/systemd/system/mc-bot.service
    ```

2.  **Add the service configuration:**
    Copy the content from the `service.template` file provided in this repository into the new service file.

    **Important:** You must edit the copied content and replace the placeholder values (`your_user`, `/path/to/your/project`) with your actual username and the correct absolute paths.

3.  **Enable and start the service:**
    ```bash
    sudo systemctl daemon-reload         # Reload systemd to recognize the new service
    sudo systemctl enable mc-bot.service # Enable the service to start on boot
    sudo systemctl start mc-bot.service  # Start the service now
    ```

4.  **Check the status:**
    You can check if the service is running correctly and view its logs:
    ```bash
    sudo systemctl status mc-bot.service
    journalctl -u mc-bot -f
    ```

The bot will start polling. To stop everything, use the `/exit` command or press `Ctrl+C` in your terminal.

## 🤖 Telegram Commands

-   `/start` - Starts the Minecraft server.
-   `/stop` - Stops the Minecraft server gracefully.
-   `/status` - Shows detailed server status, including ready state, uptime, and online players.
-   `/cmd <command>` - Executes a command on the server console (e.g., `/cmd say Hello`).
-   `/kick <player>` - Kicks a player from the server.
-   `/op <player>` - Grants operator status to a player.
-   `/help` - Displays this list of commands.
-   `/exit` - Shuts down the server and the bot.
