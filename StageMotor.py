


import serial
from PyQt5.QtCore import QObject, pyqtSignal,QThread



STAGE_PROMPT = "### STAGE info ###  \n"

def serial_init(port,baudrate=115200):
    try:
        ser = serial.Serial(port, 115200, timeout=1)
        if ser.is_open:
            print(STAGE_PROMPT + f"Serial port {port} opened successfully.")
            return ser
        else:
            print(STAGE_PROMPT + f"Failed to open serial port {port}.")
            return None
    except serial.SerialException as e:
        print(STAGE_PROMPT + f"Error opening serial port {port}: {e}")
        return None



CODE_SERVO_ON       = bytes([0x68, 0x01, 0x01, 0x01, 0x00, 0x00, 0x00, 0x0D])
CODE_SERVO_OFF      = bytes([0x68, 0x01, 0x01, 0x00, 0x00, 0x00, 0x00, 0x0D])

CODE_ALARM_RESET    = bytes([0x68, 0x01, 0x02, 0x00, 0x00, 0x00, 0x00, 0x0D])
CODE_CW_STEP        = bytes([0x68, 0x01, 0x03, 0x01, 0x00, 0x00, 0x00, 0x0D])
CODE_CCW_STEP       = bytes([0x68, 0x01, 0x04, 0x01, 0x00, 0x00, 0x00, 0x0D])

CODE_CW_VAL_STEP    = lambda x: bytes([0x68, 0x01, 0x20, x % 0xff  , x >> 8, 0x00, 0x00, 0x0D])
CODE_CCW_VAL_STEP   = lambda x: bytes([0x68, 0x01, 0x21, x % 0xff  , x >> 8, 0x00, 0x00, 0x0D])

STATE_NONE = 0
STATE_IDLE = 1
STATE_SCAN = 2


class StageMotorDevice(QObject):

    scan_ready_msg = pyqtSignal(bool)
    sync_ack_msg = pyqtSignal()
    def __init__(self):
        super().__init__()

        self.handler = None
        self.step = 100      # step can be negative. If positive, it means CW, else CCW



        """
            state enum:
            None : not open
            True : open success
        
        """
        self.state = None
    def open(self, __, port = "COM4", baudrate=115200):
        if self.state is not None :
            print(STAGE_PROMPT + "Serial port is already open.")
            return True
        else:
            self.handler = serial_init(port, baudrate)
            self.state = None if self.handler is None else STATE_IDLE
            return self.state is STATE_IDLE
    

    def close(self):
        if self.state is STATE_NONE:
            print(STAGE_PROMPT + "Stage motor is not open.")
            return True
        else:
            try:
                self.handler.close()
                self.state = STATE_NONE
                print(STAGE_PROMPT + "Stage motor serial port closed.")
                return True
            except Exception as e:
                print(STAGE_PROMPT + f"Error closing stage motor serial port: {e}")
                return False

    def servo(self, flag):
        if flag == 0:
            return self.servo_off()
        if self.state == STATE_NONE:
            print(STAGE_PROMPT + "Stage motor is not ready.")
            return False
        else:
            try:
                self.handler.write(CODE_SERVO_ON)
                return True
            except Exception as e:
                print(STAGE_PROMPT + f"Error turning on stage motor servo: {e}")
                return False
    def servo_off(self):
        if self.state == STATE_NONE:
            print(STAGE_PROMPT + "Stage motor is not ready.")
            return False
        else:
            try:
                self.handler.write(CODE_SERVO_OFF)
                return True
            except Exception as e:
                print(STAGE_PROMPT + f"Error turning off stage motor servo: {e}")
                return False

    def move_cw_step(self):
        if self.state == STATE_NONE:
            print(STAGE_PROMPT + "Stage motor is not ready.")
            return False
        else:
            try:
                self.handler.write(CODE_CW_STEP)
                return True
            except Exception as e:
                print(STAGE_PROMPT + f"Error moving stage motor clockwise: {e}")
                return False
    def move_ccw_step(self):
        if self.state == STATE_NONE:
            print(STAGE_PROMPT + "Stage motor is not ready.")
            return False
        else:
            try:
                self.handler.write(CODE_CCW_STEP)
                return True
            except Exception as e:
                print(STAGE_PROMPT + f"Error moving stage motor counter-clockwise: {e}")
                return False

    def set_step(self,step):
        
        if not isinstance(step, int):
            raise "step must be integer"

        if not (step <= 0x7ffe and step >= - 0x7ffe):
            raise "step range incorrect"

        self.step = step

    def move(self):
        if self.state == STATE_NONE:
            print(STAGE_PROMPT + "Stage motor is not ready.")
            return False
        else:
            try:
                if self.step > 0:
                    code = CODE_CW_VAL_STEP(self.step)
                    self.handler.write(code)

                elif self.step < 0:
                    code = CODE_CCW_VAL_STEP(- self.step)
                    self.handler.write(code)

                return True
            except Exception as e:
                print(STAGE_PROMPT + f"Error moving stage motor counter-clockwise: {e}")
                return False


    def start_scan(self,params):
        self.scan_params = params
        
        if self.state is STATE_IDLE :
            self.state = STATE_SCAN
            self.scan_ready_msg.emit(True)
            print("Stage is ready to scan.")
        else:
            self.state = self.state
            self.scan_ready_msg.emit(False)
            print("Stage is not ready to scan.")

    def scan_complete(self):
        if self.state is STATE_SCAN:
            self.state = STATE_IDLE
            print("Stage scan complete, back to idle.")

    def scan_sync(self):
        if self.state is STATE_SCAN:
            self.move_thread = MoveWaitThread(self, self.scan_params[0])
            self.move_thread.finished_signal.connect(self.sync_ack)
            self.move_thread.start()
    def sync_ack(self):
        if self.state is STATE_SCAN:
            self.sync_ack_msg.emit()


stageMotor_D = StageMotorDevice()


class MoveWaitThread(QThread):
    # Signals to update the UI or Logic when finished
    finished_signal = pyqtSignal()
    error_signal = pyqtSignal(str)

    def __init__(self, device, arg):
        super().__init__()
        self.handler = device
        self.arg = arg

    def run(self):
        try:
            # 1. Send the Move Command

            self.handler.set_step(int(self.arg))
            
            self.handler.move()
            
            self.msleep(90)
            # 3. Emit finished signal
            self.finished_signal.emit()
            
        except Exception as e:
            self.error_signal.emit(str(e))


