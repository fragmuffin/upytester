import uasyncio as asyncio

loop = None

def init_loop():
    global loop
    loop = asyncio.get_event_loop()

keepalive = True  # watched by mainloop, set to False to break cycle
