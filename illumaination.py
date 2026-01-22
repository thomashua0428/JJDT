
import serial
import time
from PyQt5.QtCore import pyqtSignal,QObject  # 导入自定义信号类
import pickle


ILLUMINATION_PROMPT = "### ILLUMINATION info ###  \n"

def serial_init(port,baudrate=115200):
    try:
        ser = serial.Serial(port, 115200, timeout=1)
        if ser.is_open:
            print(ILLUMINATION_PROMPT + f"Serial port {port} opened successfully.")
            return ser
        else:
            print(ILLUMINATION_PROMPT + f"Failed to open serial port {port}.")
            return None
    except serial.SerialException as e:
        print(ILLUMINATION_PROMPT + f"Error opening serial port {port}: {e}")
        return None






class IlluminationDevice(QObject):

    """
    Docstring for IlluminationDevice
    
    :1 : LED opened
    :0 : LED failed to open
    :2 : LED closed
    """

    illumination_msg = pyqtSignal(int)

    scan_ready_msg = pyqtSignal(bool)
    def __init__(self):
        super().__init__()

        self.handler = None
        
        """
            state enum:
            None : not open
            True : open success
        
        """
        self.state = None
        self.scan_params = None
    def open(self, __, port = "COM3", baudrate=115200):
        if self.state is not None :
            print(ILLUMINATION_PROMPT + "Serial port is already open.")
            return True
        else:
            self.handler = serial_init(port, baudrate)
            self.state = None if self.handler is None else True

            msg = 1 if self.state else 0
            self.illumination_msg.emit(msg)
            return self.state is not None

    def clear(self, __):
        if self.state is None:
            print(ILLUMINATION_PROMPT + "Serial port is not initialized.")
            return
        else:
            tmp = "clear"
            self.handler.write(tmp.encode())     

    def illumination_at(self, __, x):
        if self.state is None:
            print(ILLUMINATION_PROMPT + "Serial port is not initialized.")
            return
        else:
            x = int(x)

            if x <= 252 and x >= 0:

                # turn x and y into a single value
                value = x 
                tmp = str(value).zfill(4)  # Ensure the value is 4 digits long, padded with zeros if necessary        
                # 发送单个字节
                self.handler.write(("lit"+tmp).encode())
                print(ILLUMINATION_PROMPT+f"Sent: {tmp}   ","x:", x)


    def close(self):
        if self.state is None:
            print(ILLUMINATION_PROMPT + "Serial port is not initialized.")
            return
        else:
            self.handler.close()

            self.state = None
            self.handler = None
            self.illumination_msg.emit(2)

            print(ILLUMINATION_PROMPT + "Serial port closed.")

    def start_scan(self):
        self.scan_ct = 0
        self.scan_params = list(self.scan_params)
        self.scan_ready_msg.emit(True)

    def scan_sync(self):
        LED_id = self.scan_params[self.scan_ct]
        self.illumination_at(0, LED_id)
        self.scan_ct = (self.scan_ct + 1)% len(self.scan_params)
        

illumination_D =  IlluminationDevice()






