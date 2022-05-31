from STM32_Bootloader_Host import stm32_bootloader_protocol
import os
import RPi.GPIO as GPIO
import time

boot_pin = 19
nrst_pin = 26

GPIO.setmode(GPIO.BCM)

GPIO.setup(nrst_pin,GPIO.OUT)
GPIO.setup(boot_pin, GPIO.OUT)

GPIO.output(nrst_pin, GPIO.LOW)
time.sleep(0.5)
GPIO.output(boot_pin, GPIO.HIGH)
time.sleep(0.5)
GPIO.output(nrst_pin, GPIO.HIGH)
time.sleep(0.5)

bl = stm32_bootloader_protocol('/dev/serial0')
if bl.port == True:
    # Initialize firmware upload
    print('Protocol Init: ' + str(bl.init_protocol()))
    print('')
    # Protect Flash
    print(bl.read_protect())
else:
    print('Error in Serial Port')

bl.close()

GPIO.output(nrst_pin, GPIO.LOW)
time.sleep(0.5)
GPIO.output(boot_pin, GPIO.LOW)
time.sleep(0.5)
GPIO.output(nrst_pin, GPIO.HIGH)
GPIO.cleanup()

