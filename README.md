
### **Do you run your Minecraft Server on a Proxmox LXC Container?**

#### Then this might be interesting to you!

The project's target is to create a MCServerController-module that lets you direct your server
from outwards. I am planning to `include` a simple telegram bot to start, stop the server and to
perform basic operations as well as to monitor the server-stats.

### **Here is how it works yet:**
    Open the config.toml and paste all your server information needed.
    Then create a `MinecraftServerController`-object and you can launch and stop your server.
    The server will start on a detached screen.

The project is in its rare beginning and is mainly meant to be a cool starter project for
my linux home lab journey.