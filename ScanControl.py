
from pipython import GCSDevice

from PyQt5.QtCore import QObject, pyqtSignal,QThread
import os
import shutil


STATE_NONE = None
STATE_IDLE = 1
STATE_BUSY = 2


DEVICE_NOACK = 0
DEVICE_READY = 1
DEVICE_BUSY = 2


state = STATE_NONE

class ScanControlThread(QThread):

    scan_start_msg_2_stage = pyqtSignal(list)
    scan_sync_msg_2_stage = pyqtSignal()

    scan_start_msg_2_camera = pyqtSignal()
    scan_sync_msg_2_camera = pyqtSignal(str)

    scan_start_msg_2_LED = pyqtSignal()
    scan_sync_msg_2_LED = pyqtSignal()


    scan_end_msg = pyqtSignal()

    def __init__(self):
        super().__init__()

        self.stage_ready_flag = DEVICE_NOACK
        self.camera_ready_flag = DEVICE_NOACK
        self.LED_ready_flag = DEVICE_NOACK

        self.stage_ack_flag = False
        self.camera_ack_flag = False
        self.LED_ack_flag = False

        self.state = STATE_IDLE

        self.scan_exposure_time1 = 80000  # us
        self.scan_gain1 = 2
        self.scan_exposure_time2 = 160000  # us
        self.scan_gain2 = 0
        self.ifLED = False


    def load_cam_handler(self, cam_operation):
        self.obj_cam_operation = cam_operation

    def load_params1(self, scan_step, scan_step_num, LED_num,
                    scan_exposure_time1, scan_gain1):
        ### param check

        if self.state is STATE_IDLE:

            self.scan_step_num = int(scan_step_num)
            self.scan_exposure_time1 = scan_exposure_time1
            self.scan_gain1 = scan_gain1

            self.LED_num = LED_num  # ms
            self.scan_step = scan_step  # um
            self.ifLED = False

            self.state = STATE_BUSY    


            ret = self.obj_cam_operation.Set_parameter(60, scan_exposure_time1, scan_gain1)

            self.start()

    def load_params2(self, LED_num, scan_exposure_time2, scan_gain2):
        if self.state is STATE_IDLE:
       
            self.scan_step_num = 1
            self.scan_exposure_time2 = scan_exposure_time2
            self.scan_gain2 = scan_gain2

            self.LED_num = LED_num  # ms
            self.scan_step = 0  # um
            self.ifLED = True

            self.state = STATE_BUSY  

            ret = self.obj_cam_operation.Set_parameter(60, scan_exposure_time2, scan_gain2)
      
            self.start()

    def run(self):

        if self.ifLED:
            if os.path.exists("res_intensity"):
                shutil.rmtree("res_intensity")
            os.makedirs("res_intensity")
        else:
            if os.path.exists("res"):
                shutil.rmtree("res")
            os.makedirs("res")



        scan_start_msg_2_stage = [self.scan_step, self.scan_step_num]
        self.scan_start_msg_2_stage.emit(scan_start_msg_2_stage)

        ### check stage response
        while True:
            self.msleep(100)
            if self.stage_ready_flag == DEVICE_READY:
                break
            elif self.stage_ready_flag == DEVICE_BUSY:
                return
            else:
                continue

        self.scan_start_msg_2_LED.emit()
        ### check LED response
        while True:
            self.msleep(100)
            if self.LED_ready_flag == DEVICE_READY:
                break
            elif self.LED_ready_flag == DEVICE_BUSY:
                return
            else:
                continue       
        
        ### delete the result under res directory



        for pos in range(self.scan_step_num):
            self.scan_sync_msg_2_stage.emit()
            
            while True:
                if  self.stage_ack_flag:
                    self.stage_ack_flag = False
                    break
                self.msleep(4)

            ### at each position, scan all LEDs
            for __ in range(self.LED_num):

                ### LED trigger
                self.LED_ack_flag = False
                self.scan_sync_msg_2_LED.emit()
                while not self.LED_ack_flag:
                    self.msleep(5)

                ### camera trigger
                self.camera_ack_flag = False
                if self.ifLED:
                    self.scan_sync_msg_2_camera.emit(f"./res_intensity/pos_{pos}-LED_{__}")
                else:
                    self.scan_sync_msg_2_camera.emit(f"./res/pos_{pos}-LED_{__}")
                while not self.camera_ack_flag:
                    self.msleep(5)


            print(f"Scanning at position: {pos}")



        # scan completed
        self.scan_end_msg.emit()
        self.state = STATE_IDLE


    def set_stage_ready(self, ready: bool):
        print(f"Stage ready status set to: {ready}")
        if ready:
            self.stage_ready_flag = DEVICE_READY
        else:
            self.stage_ready_flag = DEVICE_BUSY

    def stage_sync_ack(self):
        self.stage_ack_flag = True


    def set_camera_ready(self, ready: bool):
        if ready:
            self.camera_ready_flag = DEVICE_READY
        else:
            self.camera_ready_flag = DEVICE_BUSY

    def camera_sync_ack(self):
        self.camera_ack_flag = True

    def set_LED_ready(self, ready: bool):
        if ready:
            self.LED_ready_flag = DEVICE_READY
        else:
            self.LED_ready_flag = DEVICE_BUSY

    def LED_sync_ack(self):
        self.LED_ack_flag = True


    def scan_abort(self):
        if self.state is STATE_BUSY:
            self.state = STATE_IDLE
            self.stage_ready_flag = DEVICE_NOACK
            self.camera_ready_flag = DEVICE_NOACK
            self.scan_end_msg.emit()
            
        



scan_D = ScanControlThread()




