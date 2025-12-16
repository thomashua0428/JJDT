from pipython import GCSDevice

from PyQt5.QtCore import QObject, pyqtSignal,QThread

STATE_NONE = None
STATE_IDLE = 1
STATE_BUSY = 2

class StageDevice(QObject):

    """
    Docstring for StageDevice
    
    :0 : Stage failed to open
    :1 : Stage opened
    :2 : Stage closed
    """

    stage_msg = pyqtSignal(int)

    velocity_msg = pyqtSignal(float)

    step_msg = pyqtSignal(float)
    def __init__(self):
        super().__init__()

        self.handler = None
        """
            state enum:
            None : not open
            1 : idle
            2 : busy
        """
        self.state = STATE_NONE
        self.step = 0    
        self.velocity = 0.0
        self.axis = '1' 

        self.thread_upload = StageThread(self)
        self.thread_upload.start()

    def open(self, __):
        if self.state is not STATE_NONE:
            print("Stage is already open.")
            return True
        else:
            pidevice = GCSDevice()
            try:    
                pidevice.InterfaceSetupDlg()
                print('connected: {}'.format(pidevice.qIDN().strip()))
                self.handler = pidevice
                self.state = 1
                self.velocity = self.get_velocity()
                self.set_step(0.1)

                self.stage_msg.emit(1)

            except Exception as e:
                print("Error connecting to stage:", e)
                self.stage_msg.emit(0)
    def close(self,__):
        if self.handler is not None:
            try:
                self.handler.CloseConnection()
                self.handler = None
                self.state = STATE_NONE
                ## close thread
                self.thread_upload.requestInterruption()
                self.thread_upload.wait()
                self.stage_msg.emit(2)
            except Exception as e:
                print("Error closing stage:", e)


    def servo_on(self,state):
        if self.state is not STATE_NONE:
            try:
                if state == 0:
                    self.handler.SVO('1', 0)
                elif state == 2:
                    self.handler.SVO('1', 1)
            except Exception as e:
                print("Error turning on stage servo:", e)

    def move_to_target(self, target_pos):
        if self.state is not STATE_NONE:
            # Set state to BUSY
            self.state = STATE_BUSY
            
            # Create the thread instance
            self.move_thread = MoveWaitThread(self, target_pos, 'MOV')
            
            # Connect signals to handle completion
            self.move_thread.finished_signal.connect(self.on_move_finished)
            self.move_thread.error_signal.connect(self.on_move_error)
            
            # Start the thread
            self.move_thread.start()

    def on_move_finished(self):
        if self.state is STATE_BUSY:
            print("Target Reached!")
            self.state = STATE_IDLE

    def on_move_error(self, error_msg):
        print(f"Error during move: {error_msg}")
        self.state = STATE_IDLE

    def set_velocity(self, velocity):
        if self.state is not STATE_NONE:
            try:
                self.handler.VEL('1', velocity)
                self.velocity = velocity
                self.velocity_msg.emit(velocity)
            except Exception as e:
                print("Error setting stage velocity:", e)
    def get_velocity(self):
        if self.state is not STATE_NONE:
            try:
                vel = self.handler.qVEL()
                vel = float(vel['1'])
                self.velocity_msg.emit(vel)
                return vel
            except Exception as e:
                print("Error getting stage velocity:", e)
                return 0.0
    
    def set_step(self, step):
        if self.state is not STATE_NONE:

            self.step = step
            self.step_msg.emit(step)
    
    def get_step(self):
        if self.state is not STATE_NONE:
            return self.step
        return 0.0

    def move_relative(self, direction):
        if self.state is not STATE_NONE:
            try:
                # Set state to BUSY
                self.state = STATE_BUSY
                
                # Create the thread instance
                self.move_thread = MoveWaitThread(self, self.step * direction, 'MVR')
                
                # Connect signals to handle completion
                self.move_thread.finished_signal.connect(self.on_move_finished)
                self.move_thread.error_signal.connect(self.on_move_error)
                
                # Start the thread
                self.move_thread.start()
            except Exception as e:
                print("Error moving stage relatively:", e)


### define a thread to update stage position

class StageThread(QThread):
    stage_position_msg = pyqtSignal(float,bool)

    def __init__(self, stage_device):
        super().__init__()
        self.stage_device = stage_device

    def run(self):
        # Run until an interruption is requested; thread can be stopped by calling requestInterruption()
        while not self.isInterruptionRequested():
            if self.stage_device.state is not STATE_NONE: 
                try:
                    val = self.stage_device.handler.qPOS()

                    ontarget_flag = all(self.stage_device.handler.qONT(self.stage_device.axis).values())

                    self.stage_position_msg.emit(float(val['1']), ontarget_flag)
                except Exception as e:
                    print("Error reading stage position:", e)
            # sleep briefly to avoid busy loop
            self.msleep(100)
            
class MoveWaitThread(QThread):
    # Signals to update the UI or Logic when finished
    finished_signal = pyqtSignal()
    error_signal = pyqtSignal(str)

    def __init__(self, device, arg,mode):
        super().__init__()
        self.handler = device.handler
        self.axis = device.axis
        self.arg = arg
        self.mode = mode
    def run(self):
        try:
            # 1. Send the Move Command

            if self.mode == 'MOV':
                self.handler.MOV(self.axis, self.arg)
            elif self.mode == 'MVR':
                self.handler.MVR(self.axis, self.arg)
            
            # 2. Loop qONT until the device is "On Target"
            # .values() returns a list of booleans, we wait until all are True
            while not all(self.handler.qONT(self.axis).values()):
                if self.isInterruptionRequested():
                    return
                self.msleep(20)  # Sleep 50ms to save CPU
            
            # 3. Emit finished signal
            self.finished_signal.emit()
            
        except Exception as e:
            self.error_signal.emit(str(e))







D_stage = StageDevice()




