import pyb
from upyt.cmd import instruction, remote
import uasyncio as asyncio


@instruction('async_blink')
async def async_blink(led_index: int):
    led = pyb.LED(led_index)
    for _ in range(3):
        led.on()
        await asyncio.sleep_ms(5)
        led.off()
        await asyncio.sleep_ms(5)


@remote
class MyLED:
    def __init__(self, led_index: int):
        self.led = pyb.LED(led_index)

    async def blink(self):
        import time
        for _ in range(3):
            self.led.on()
            #time.sleep_ms(5)
            await asyncio.sleep_ms(5)
            self.led.off()
            #time.sleep_ms(5)
            await asyncio.sleep_ms(5)
