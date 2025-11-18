
### **Do you run your Minecraft Server on a Proxmox LXC Container?**

#### Then this might be interesting to you!

The project's target is to create a MCServerController-module that lets you direct your server
from outwards. I am planning to `include` a simple telegram bot to start, stop the server and to
perform basic operations as well as to monitor the server-stats.

### **Here is how it works yet:**
Open the config.toml and paste all your server information needed.

Let's say:
    `config = load_config()`\n
    `msc = MinecraftServerController(config)`\n
    `msc.start()`\n
    `msc.stop()`
    
