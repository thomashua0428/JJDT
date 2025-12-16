from pipython import GCSDevice

from PyQt5.QtCore import QObject, pyqtSignal,QThread



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
        self.state = None
        self.step = 0    
        self.velocity = 0.0
        self.thread_upload = StageThread(self)
        self.thread_upload.start()

    def open(self, __):
        if self.state is not None :
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
                self.state = None
                ## close thread
                self.thread_upload.requestInterruption()
                self.thread_upload.wait()
                self.stage_msg.emit(2)
            except Exception as e:
                print("Error closing stage:", e)


    def servo_on(self,__):
        if self.state is not None:
            try:
                self.handler.SVO('1', 1)
            except Exception as e:
                print("Error turning on stage servo:", e)
    

    def move_to_target(self, target_pos):
        if self.state is not None:
            try:
                self.state = 2
                self.handler.MOV('1', target_pos)
                self.state = 1
            except Exception as e:
                print("Error moving stage to target position:", e)


    def set_velocity(self, velocity):
        if self.state is not None:
            try:
                self.handler.VEL('1', velocity)
                self.velocity = velocity
                self.velocity_msg.emit(velocity)
            except Exception as e:
                print("Error setting stage velocity:", e)
    def get_velocity(self):
        if self.state is not None:
            try:
                vel = self.handler.qVEL()
                vel = float(vel['1'])
                self.velocity_msg.emit(vel)
                return vel
            except Exception as e:
                print("Error getting stage velocity:", e)
                return 0.0
    
    def set_step(self, step):
        self.step = step
        self.step_msg.emit(step)
    
    def get_step(self):
        return self.step
    
    def move_relative(self, direction):
        if self.state is not None:
            try:
                self.handler.MVR('1', self.step * direction)
            except Exception as e:
                print("Error moving stage relatively:", e)


### define a thread to update stage position

class StageThread(QThread):
    stage_position_msg = pyqtSignal(float)

    def __init__(self, stage_device):
        super().__init__()
        self.stage_device = stage_device

    def run(self):
        # Run until an interruption is requested; thread can be stopped by calling requestInterruption()
        while not self.isInterruptionRequested():
            if self.stage_device.state is not None :
                try:
                    val = self.stage_device.handler.qPOS()
                    self.stage_position_msg.emit(float(val['1']))
                except Exception as e:
                    print("Error reading stage position:", e)
            # sleep briefly to avoid busy loop
            self.msleep(100)
            



D_stage = StageDevice()




