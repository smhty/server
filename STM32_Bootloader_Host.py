import time
import serial 
from serial import SerialException
import threading
# -----------------------------------------------------------------------------------
class readbusThread (threading.Thread):
    nbytes = 0
    trig = 0
    kill = 0

    def __init__(self, connection):
        threading.Thread.__init__(self)
        self.connection = connection

    def run(self):
        while self.kill == 0:
            if self.trig == 1:
                self.rec_bytes = self.connection.read(self.nbytes)
                self.trig = 0
# -----------------------------------------------------------------------------------
class stm32_bootloader_protocol :
    def __init__(self, port):
        self.ACK = 0x79
        self.NACK = 0x1F
        try:
            self.ser = serial.Serial(port)
            self.ser.baudrate = 115200
            self.ser.parity = serial.PARITY_EVEN
            self.ser.stopbits = serial.STOPBITS_ONE
            self.ser.timeout = 10
            self.read_thread = readbusThread(self.ser)
            self.read_thread.start()
            self.chip_id = [0]*12
            self.port = True
        except SerialException:
            self.port = False
    
    # Initialize Protocol:
    #   Initializes the firmware upgrade protocol.
    def init_protocol(self):
        resp = False
        self.read_thread.nbytes = 1
        self.read_thread.trig = 1
        self.ser.write(bytes([0x7F]))    # Start communication
        while self.read_thread.trig == 1:
            pass
        if len(self.read_thread.rec_bytes) == self.read_thread.nbytes:
            if self.read_thread.rec_bytes[0] == self.ACK:
                resp = True
        return resp

    # Get command:
    #   The Get command allows the user to get the version of the bootloader and the supported
    #   commands.
    def get(self):
        print('Get Command Resp: ')
        resp = False
        cmd = [0x00, 0xFF]
        self.read_thread.nbytes = 1
        self.read_thread.trig = 1
        self.ser.write(bytes(cmd)) 
        while self.read_thread.trig == 1:
            pass
        if len(self.read_thread.rec_bytes) == self.read_thread.nbytes:
            if self.read_thread.rec_bytes[0] == self.ACK:
                self.read_thread.trig = 1
                while self.read_thread.trig == 1:
                    pass
                self.read_thread.nbytes = self.read_thread.rec_bytes[0] + 2
                self.read_thread.trig = 1
                while self.read_thread.trig == 1:
                    pass
                for i in range(len(self.read_thread.rec_bytes) -1 ):
                    print('\tByte %i: 0X%x '%(i+3, self.read_thread.rec_bytes[i]))
                if len(self.read_thread.rec_bytes) == self.read_thread.nbytes:
                    if self.read_thread.rec_bytes[-1] == self.ACK:
                        resp = True
        print('')
        return resp

    # Get Version:
    #   The Get Version & Read Protection Status command is used to get the bootloader version
    #   and the read protection status.
    def get_ver(self):
        print('Get Version Command Resp: ')
        resp = False
        cmd = [0x01, 0xFE]
        self.read_thread.nbytes = 4
        self.read_thread.trig = 1
        self.ser.write(bytes(cmd)) 
        while self.read_thread.trig == 1:
            pass
        if len(self.read_thread.rec_bytes) == self.read_thread.nbytes:
            if self.read_thread.rec_bytes[0] == self.ACK:
                for i in range(1,len(self.read_thread.rec_bytes)):
                    print('\tByte %i: 0X%x '%(i+1, self.read_thread.rec_bytes[i]))
                if len(self.read_thread.rec_bytes) == self.read_thread.nbytes:
                    if self.read_thread.rec_bytes[-1] == self.ACK:
                        resp = True
        print('')
        return resp

    # Get ID:
    #   The Get ID command is used to get the version of the chip ID (identification). When the
    #   bootloader receives the command, it transmits the product ID to the host.
    def get_id(self):
        print('Get ID Command Resp: ')
        resp = False
        cmd = [0x02, 0xFD]
        self.read_thread.nbytes = 3
        self.read_thread.trig = 1
        self.ser.write(bytes(cmd)) 
        while self.read_thread.trig == 1:
            pass
        if len(self.read_thread.rec_bytes) == self.read_thread.nbytes:
            if self.read_thread.rec_bytes[0] == self.ACK:
                print('\tByte 2: 0X%x '%self.read_thread.rec_bytes[2])
                self.read_thread.nbytes = self.read_thread.rec_bytes[2] + 1
                self.read_thread.trig = 1
                while self.read_thread.trig == 1:
                    pass
                for i in range(len(self.read_thread.rec_bytes)):
                    print('\tByte %i: 0X%x '%(i+3, self.read_thread.rec_bytes[i]))
                if len(self.read_thread.rec_bytes) == self.read_thread.nbytes:
                    if self.read_thread.rec_bytes[-1] == self.ACK:
                        resp = True
        print('')
        return resp

    # Get Device ID:
    #  Reads the unique device id from the memory. Please note that base id might be different
    #  for other STM32 microcontrollers.
    def get_device_id(self):
        base_address_h7 = [0x1F, 0xF1, 0xE8, 0x00]  
        self.read_mem(self.chip_id, base_address_h7, 12)
        return bytes(self.chip_id)

    # Read Memory:
    #   The Read Memory command is used to read data from any valid memory address in RAM, 
    #   Flash memory and the information block (system memory or option byte areas).
    def read_mem(self, buff, address_bytes, nbytes_to_read):
        resp = False
        cmd = [0x11, 0xEE]
        self.read_thread.nbytes = 1
        self.read_thread.trig = 1
        self.ser.write(bytes(cmd)) 
        while self.read_thread.trig == 1:
            pass
        if len(self.read_thread.rec_bytes) == self.read_thread.nbytes:
            if self.read_thread.rec_bytes[0] == self.ACK:
                address_check_sum = 0
                for i in range(4):
                    address_check_sum = address_check_sum ^ address_bytes[i]
                self.read_thread.nbytes = 1
                self.read_thread.trig = 1
                self.ser.write(bytes(address_bytes + [address_check_sum]))
                while self.read_thread.trig == 1:
                    pass
                if len(self.read_thread.rec_bytes) == self.read_thread.nbytes:
                    if self.read_thread.rec_bytes[0] == self.ACK:
                        self.read_thread.nbytes = nbytes_to_read + 1
                        self.read_thread.trig = 1
                        self.ser.write(bytes([nbytes_to_read-1] + [(nbytes_to_read-1) ^ 0xFF])) 
                        while self.read_thread.trig == 1:
                            pass
                        if len(self.read_thread.rec_bytes) == self.read_thread.nbytes:
                            if self.read_thread.rec_bytes[0] == self.ACK:
                                # buff = self.read_thread.rec_bytes[1:]
                                for i in range(nbytes_to_read):
                                    buff[i] = self.read_thread.rec_bytes[i+1]
                                resp = True
        return resp

    # Go:
    #   The Go command is used to execute the downloaded code or any other code by branching
    #   to an address specified by the application. 
    def go(self, address):
        pass

    # Write Memory:
    #   The Write Memory command is used to write data to any valid memory address
    #   i.e. RAM, Flash memory, or option byte area.
    def write_mem(self, firmware):
        resp = False
        if len(firmware)%4 == 0:
            percent = 0
            nb_packets = len(firmware)//256
            if len(firmware)%256 != 0:
                nb_packets = nb_packets + 1
            cmd = [0x31, 0xCE]
            buff = [i for i in firmware]
            download_cplt = False
            address = 0x08000000
            while download_cplt == False:
                resp = False # Reset resp flag before each write process
                data_to_write = buff[:256]
                address_bytes = [(address>>24) & 0xFF, (address>>16) & 0xFF, (address>>8) & 0xFF, (address) & 0xFF]
                address_check_sum = 0
                for i in range(4):
                    address_check_sum = address_check_sum ^ address_bytes[i]
                address = address + 256
                check_sum = len(data_to_write)-1
                for i in range(len(data_to_write)):
                    check_sum = check_sum ^ data_to_write[i]
                self.read_thread.nbytes = 1
                self.read_thread.trig = 1
                self.ser.write(bytes(cmd)) 
                while self.read_thread.trig == 1:
                    pass
                if len(self.read_thread.rec_bytes) == self.read_thread.nbytes:
                    if self.read_thread.rec_bytes[0] == self.ACK:
                        self.read_thread.trig = 1
                        self.ser.write(bytes(address_bytes + [address_check_sum]))
                        while self.read_thread.trig == 1:
                            pass
                        if len(self.read_thread.rec_bytes) == self.read_thread.nbytes:
                            if self.read_thread.rec_bytes[0] == self.ACK:
                                self.read_thread.nbytes = 1
                                self.read_thread.trig = 1
                                self.ser.write(bytes([len(data_to_write)-1] + data_to_write + [check_sum]))
                                while self.read_thread.trig == 1:
                                    pass
                                if len(self.read_thread.rec_bytes) == self.read_thread.nbytes:
                                    if self.read_thread.rec_bytes[0] == self.ACK:
                                        resp = True
                buff = buff[256:]
                percent = percent + 1
                print('Progress = %i%%'%((percent/nb_packets)*100))
                if len(buff) == 0 or resp == False:
                    download_cplt = True
        return resp
    
    # Erase Memory:
    #   The Erase Memory command allows the host to erase Flash memory pages.
    def erase_mem(self,number_of_pages, page_numbers):
        pass

    # Extended Full Erase:
    #   The Extended Erase Memory command allows the host to erase Flash memory pages using
    #   two bytes addressing mode.
    def extended_full_erase(self):
        resp = False
        cmd = [0x44, 0xBB]
        self.read_thread.nbytes = 1
        self.read_thread.trig = 1
        self.ser.write(bytes(cmd)) 
        while self.read_thread.trig == 1:
            pass
        if len(self.read_thread.rec_bytes) == self.read_thread.nbytes:
            if self.read_thread.rec_bytes[0] == self.ACK:
                self.read_thread.trig = 1
                self.ser.timeout = 120
                self.ser.write(bytes([0xFF, 0xFF, 0x00])) 
                while self.read_thread.trig == 1:
                    pass
                if len(self.read_thread.rec_bytes) == self.read_thread.nbytes:
                    if self.read_thread.rec_bytes[0] == self.ACK:
                        resp = True
        self.ser.timeout = 4
        return resp
    
    # Write Protect:
    #   The Write Protect command is used to enable the write protection for some or all Flash
    #   memory sectors.    
    def write_protect(self):
        pass

    # Write Unprotect:
    #   The Write Unprotect command is used to disable the write protection of all the Flash
    #   memory sectors.   
    def write_unprotect(self):
        pass

    # Readout Protect:
    #   The Readout Protect command is used to enable the Flash memory read protection.    
    def read_protect(self):
        resp = False
        cmd = [0x82, 0x7D]
        self.read_thread.nbytes = 2
        self.read_thread.trig = 1
        self.ser.write(bytes(cmd)) 
        while self.read_thread.trig == 1:
            pass
        if len(self.read_thread.rec_bytes) == self.read_thread.nbytes:
            if self.read_thread.rec_bytes[0] == self.ACK and self.read_thread.rec_bytes[1] == self.ACK:
                resp = True
        return resp

    # Readout Unprotect:
    #   The Readout Unprotect command is used to disable the Flash memory read protection.    
    def read_unprotect(self):
        resp = False
        cmd = [0x92, 0x6D]
        self.read_thread.nbytes = 2
        self.read_thread.trig = 1
        self.ser.write(bytes(cmd)) 
        while self.read_thread.trig == 1:
            pass
        if len(self.read_thread.rec_bytes) == self.read_thread.nbytes:
            if self.read_thread.rec_bytes[0] == self.ACK and self.read_thread.rec_bytes[1] == self.ACK:
                resp = True
        return resp
    
    # Close:
    #   Closes all the open files, threads and ports.
    def close(self):
        self.read_thread.kill = 1
        self.ser.close()
# -----------------------------------------------------------------------------------
