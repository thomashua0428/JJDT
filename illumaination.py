import serial
import time
from PyQt5.QtCore import pyqtSignal,QObject,QThread  # 导入自定义信号类
import pickle   


ILLUMINATION_PROMPT = "### ILLUMINATION info ###  \n"

def serial_init(port,baudrate=115200):
    try:
        # use the provided baudrate and non-blocking mode (timeout=0)
        ser = serial.Serial(port, baudrate, timeout=0)
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
    LED_set_complete_signal = pyqtSignal()
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
        self.thread = IlluminationThread(self)
        self.LED_set_flag = False
        
        # don't start the thread immediately to avoid busy-loop at startup;
        # start it when serial port is successfully opened in open()
        # self.thread will be started inside open()
    def open(self, __, port = "COM3", baudrate=115200):
        if self.state is not None :
            print(ILLUMINATION_PROMPT + "Serial port is already open.")
            return True
        else:
            self.handler = serial_init(port, baudrate)
            self.state = None if self.handler is None else True

            # start background thread only after a successful open
            if self.state and not self.thread.isRunning():
                self.thread.start()

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
        self.LED_set_flag = True


# this thread wait back information from serial port

class IlluminationThread(QThread):

    def __init__(self, illumination_device):
        super().__init__()
        self.illumination_device = illumination_device

    def run(self):
        # main loop: when idle sleep longer to avoid busy-wait; when open poll serial
        while True:
            try:
                # idle if device not opened or handler missing
                if self.illumination_device.state is None or self.illumination_device.handler is None:
                    # sleep to avoid busy-loop and give CPU back
                    self.msleep(20)
                    continue

                # handler exists and device is open: poll input with short sleeps
                handler = self.illumination_device.handler
                # read all available bytes at once to avoid blocking on readline()
                if hasattr(handler, "in_waiting") and handler.in_waiting > 0:
                    data = handler.read(handler.in_waiting)
                    if data:
                        text = data.decode(errors='ignore')
                        # normalize and split into lines (handle \r, \n, or \r\n)
                        lines = text.replace('\r', '\n').split('\n')
                        for raw in lines:
                            line = raw.strip()
                            if not line:
                                continue
                            if self.illumination_device.LED_set_flag:
                                self.illumination_device.LED_set_flag = False
                                self.illumination_device.LED_set_complete_signal.emit()
                            print(ILLUMINATION_PROMPT + f"Received: {line}")
                # smaller pause for quicker responsiveness
                self.msleep(10)
            except Exception as e:
                # protect thread from crashing; log and sleep a bit before retry
                print(ILLUMINATION_PROMPT + f"Thread error: {e}")
                self.msleep(200)
illumination_D =  IlluminationDevice()






