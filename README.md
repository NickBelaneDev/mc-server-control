
# 🤖 Minecraft Server Telegram Controller

A simple Python bot to manage your Minecraft server via Telegram. Start, stop, and check the status of your server from anywhere. Perfect for headless Linux servers.

 <!-- It's a good idea to add a small GIF showing the bot in action! -->

## ✨ Features

-   **🚀 Remote Control:** Start and stop your server with simple commands.
-   **📊 Live Status:** Get real-time status, including player count and a list of online players.
-   **⚙️ Background Operation:** Uses `screen` to run the server reliably in the background.
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
    git clone <your-repository-url>
    cd minecraft-server
    ```

2.  **Install dependencies:**
    ```bash
    python -m venv .venv
    source .venv/bin/activate # On Windows, use .venv\Scripts\activate
    pip install -r requirements.txt
    ```

3.  **Set up your bot:**
    -   Get a token from [BotFather](https://t.me/BotFather) on Telegram.
    -   Copy `empty.env` to `.env` and add your token:
    ```bash
    cp empty.env .env
    ```
    ```.env
    BOT_TOKEN='YOUR_SECRET_TOKEN_HERE'
    ```

4.  **Configure your server:**
    -   Edit `config.toml` with the **absolute path** to your server directory and other settings.
    ```toml
    [mc]
    dir = "/home/user/minecraft/my_server"
    jar = "paper-1.21-10.jar"
    min_gb = 4
    max_gb = 4
    screen_name = "minecraft_server"
    ```

5.  **Run the bot:**
    ```bash
    python main.py
    ```

The bot will start polling. To stop everything, use the `/exit` command or press `Ctrl+C` in your terminal.

## 🤖 Telegram Commands

-   `/start` - Starts the Minecraft server.
-   `/stop` - Stops the Minecraft server gracefully.
-   `/status` - Shows server status, uptime, and online players.
-   `/help` - Displays this list of commands.
-   `/exit` - Shuts down the server and the bot.
