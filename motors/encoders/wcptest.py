import spidev
import time

spi = spidev.SpiDev()
spi.open(0, 0)
spi.max_speed_hz = 500000

pos = [0x00,0x00]
reset = [0x00,0x60]
zero = [0x00,0x70]
##SET OTHER PINS MANUALLY?

i = 0
rep1 = 0

while i < 10:
    val = spi.xfer2(pos)
    if len(val) != 2:
        print("ERROR")
        sleep(1)
        continue
    rep1 = val[0]<<8
    rep1 |= val[1]
    print(bin(rep1), rep1 & 0x3FFF)
    time.sleep(1)
    i += 1


spi.close()
exit()

