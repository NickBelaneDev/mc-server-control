from src.config_loader import load_config
from src.services import MinecraftServerController

import logging

logging.basicConfig(level=logging.INFO,
                    format="%(asctime)s - %(levelname)s - %(message)s"
                    )

if __name__ == "__main__":
    config = load_config()
    msc = MinecraftServerController(config)
    msc.start()

