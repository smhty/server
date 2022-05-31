from STM32_Bootloader_Host import stm32_bootloader_protocol
from Crypto.Cipher import AES
import hashlib
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

script_path = os.path.dirname(os.path.realpath(__file__))
sha1 = hashlib.sha1()
key = bytes('WhySoSerious^@@^','utf-8')

log = open(script_path + '/log.txt', 'w')
log.write('Firmware Upgrade Started...\n')

if os.path.exists(script_path + '/efirmware') == True:
    fid = open(script_path + '/efirmware', 'rb')
    encrypted_text = fid.read()
    fid.close()

    sha1.update(encrypted_text[40:])
    HASH = format(sha1.hexdigest())
    if HASH.encode() == encrypted_text[:40]:
        decipher = AES.new(key, AES.MODE_CBC, IV=encrypted_text[40:56])
        firmware = decipher.decrypt(encrypted_text[56:])
        bl = stm32_bootloader_protocol('/dev/serial0')
        if bl.port == True:
            # Initialize firmware upload
            if bl.init_protocol() == True:
                log.write('Portocol Init: True\n')
                if bl.extended_full_erase() == True:
                    if bl.write_mem(firmware) == True:
                        log.write('Firmware Upgraded Successfuly.\n')
                    else:
                        log.write('Write: False \n')
                        log.write('Firmware Upgrade Failed.\n')

                else:
                    log.write('Erase: False \n')
                    log.write('Firmware Upgrade Failed.\n')
            else:
                log.write('Portocol Init: False\n')
                log.write('Firmware Upgrade Failed.\n')
            bl.close()
        else:
            log.write('Error in Serial Port of RPI.\n')
            log.write('Firmware Upgrade Failed.\n')
    else:
        log.write('Firmware file is not valid.\n')
        log.write('Firmware Upgrade Failed.\n')
    log.close()
else:
    log.write('Firmware file not found.\n')
    log.write('Firmware Upgrade Failed.\n')
    log.close()

GPIO.output(nrst_pin, GPIO.LOW)
time.sleep(0.5)
GPIO.output(boot_pin, GPIO.LOW)
time.sleep(0.5)
GPIO.output(nrst_pin, GPIO.HIGH)
GPIO.cleanup()
print('End of Firmware Upgrade Script')
