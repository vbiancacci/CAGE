import RPi.GPIO as GPIO
import spidev
import time

spi = spidev.SpiDev()
spi.open(0, 0)
spi.max_speed_hz = 200000

GPIO.setmode(GPIO.BOARD)
GPIO.setup(13, GPIO.OUT)
GPIO.output(13, GPIO.HIGH)

pos = [0x00, 0x00]
reset = [0x00, 0x60]
zero = [0x00, 0x70]

GPIO.output(13, GPIO.LOW)
time.sleep(0.075)

val = spi.xfer2(pos)

time.sleep(0.075)
GPIO.output(13, GPIO.HIGH)

if len(val) != 2:
    print("ERROR")
    sleep(1)
reply = val[0]<<8
reply |= val[1]
time.sleep(2)

time.sleep(0.075)
GPIO.output(13, GPIO.LOW)

val = spi.xfer2(zero)

time.sleep(0.075)
GPIO.output(13, GPIO.HIGH)

time.sleep(3)
if len(val) != 2:
    print("ERROR")
    sleep(1)
reply = val[0]<<8
reply |= val[1]
print(reply & 0x3FFF)
time.sleep(2)

GPIO.cleanup()
spi.close()
exit()
