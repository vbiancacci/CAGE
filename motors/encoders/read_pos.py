import spidev
import time

spi = spidev.SpiDev()
spi.open(0, 0)
spi.max_speed_hz = 200000

pos = [0x00,0x00]
reset = [0x00,0x60]
zero = [0x00,0x70]
print("Life is pain. Anyone who tells you differently is selling something.")
i = 0
rep1 = 0

while True:
    val = spi.xfer2(pos)
    if len(val) != 2:
        print("ERROR")
        sleep(1)
        continue
    rep1 = val[0]<<8
    rep1 |= val[1]
    #print(bin(rep1), rep1 & 0x3FFF)
    print(rep1 & 0x3FFF)
    time.sleep(1)


spi.close()
exit()
