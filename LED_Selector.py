import sys
import math
import pickle
from PyQt5.QtWidgets import (QApplication, QWidget, QPushButton, QVBoxLayout, 
                             QHBoxLayout, QMessageBox, QFrame, QScrollArea, 
                             QFileDialog, QComboBox, QLabel, QGroupBox, QSpinBox) # 新增 QSpinBox
from PyQt5.QtCore import Qt

class LED_Selector(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle('ODT 系统 LED 阵列控制器 v3.0')
        self.resize(1000, 980) 

        # 定义圆环参数
        self.ring_counts = [1, 12, 24, 36, 48, 60, 72] 
        self.led_buttons = [] 
        
        # 布局参数
        self.center_x = 420
        self.center_y = 420
        self.base_radius_step = 50
        self.btn_size = 30

        self.initUI()

    def initUI(self):
        main_layout = QVBoxLayout()
        
        # --- 1. 上方：LED 阵列显示区 ---
        self.canvas = QFrame()
        self.canvas.setMinimumSize(840, 840)
        self.canvas.setStyleSheet("background-color: #2b2b2b;") 
        
        self.create_led_array()
        
        scroll = QScrollArea()
        scroll.setWidget(self.canvas)
        scroll.setWidgetResizable(True)
        main_layout.addWidget(scroll)

        # --- 2. 下方：功能控制区 ---
        control_group = QGroupBox("控制面板")
        control_group.setStyleSheet("QGroupBox { font-weight: bold; font-size: 14px; }")
        control_layout = QHBoxLayout()

        # A. 圆环/间隔选择功能
        ring_layout = QHBoxLayout()
        
        # 圆环选择下拉框
        lbl_ring = QLabel("选择圆环:")
        self.combo_rings = QComboBox()
        for i, count in enumerate(self.ring_counts):
            self.combo_rings.addItem(f"第 {i} 圈 ({count}个)")
        
        # 间隔设置输入框 (新增)
        lbl_interval = QLabel("间隔数:")
        self.spin_interval = QSpinBox()
        self.spin_interval.setRange(0, 50) # 设置范围，比如 0 到 50
        self.spin_interval.setValue(0)     # 默认 0 (不跳过)
        self.spin_interval.setToolTip("0=连续选择, 1=隔1个选1个, 2=隔2个选1个...")
            
        self.btn_select_ring = QPushButton("应用选择")
        self.btn_select_ring.clicked.connect(lambda: self.set_ring_state(True))
        
        self.btn_clear_ring = QPushButton("清除该圈")
        self.btn_clear_ring.clicked.connect(lambda: self.set_ring_state(False))

        ring_layout.addWidget(lbl_ring)
        ring_layout.addWidget(self.combo_rings)
        ring_layout.addSpacing(15)
        ring_layout.addWidget(lbl_interval)
        ring_layout.addWidget(self.spin_interval)
        ring_layout.addSpacing(15)
        ring_layout.addWidget(self.btn_select_ring)
        ring_layout.addWidget(self.btn_clear_ring)
        
        # B. 全局操作
        global_layout = QHBoxLayout()
        self.btn_clear_all = QPushButton("全局清除")
        self.btn_clear_all.setStyleSheet("background-color: #d9534f; color: white;")
        self.btn_clear_all.clicked.connect(self.clear_all_leds)

        self.btn_export = QPushButton("导出(Pickle)")
        self.btn_export.setStyleSheet("background-color: #5bc0de; color: white;")
        self.btn_export.clicked.connect(self.export_leds_pickle)

        global_layout.addWidget(self.btn_clear_all)
        global_layout.addWidget(self.btn_export)

        # 布局组合
        # 注意 stretch 参数，让左侧的控制区占更多空间
        control_layout.addLayout(ring_layout, stretch=3) 
        control_layout.addSpacing(20)
        control_layout.addLayout(global_layout, stretch=1) 

        control_group.setLayout(control_layout)
        main_layout.addWidget(control_group)

        self.setLayout(main_layout)

    def create_led_array(self):
        led_id_counter = 0 
        for ring_index, count in enumerate(self.ring_counts):
            current_radius = ring_index * self.base_radius_step
            
            if ring_index == 0:
                # 传入 intra_ring_index (圈内序号) 为 0
                self.add_led_button(self.center_x, self.center_y, led_id_counter, ring_index, 0)
                led_id_counter += 1
                continue

            angle_step = 360 / count
            for i in range(count):
                angle_deg = i * angle_step - 90 
                angle_rad = math.radians(angle_deg)
                x = self.center_x + current_radius * math.cos(angle_rad)
                y = self.center_y + current_radius * math.sin(angle_rad)

                # 传入 intra_ring_index 为 i
                self.add_led_button(x, y, led_id_counter, ring_index, i)
                led_id_counter += 1

    def add_led_button(self, x, y, led_id, ring_index, intra_index):
        btn = QPushButton(str(led_id), self.canvas)
        btn.setGeometry(int(x - self.btn_size/2), int(y - self.btn_size/2), self.btn_size, self.btn_size)
        btn.setCheckable(True)
        
        # 存储属性：ID, 环号, 环内序号(0~N)
        btn.setProperty("led_id", led_id) 
        btn.setProperty("ring_index", ring_index)
        btn.setProperty("intra_index", intra_index) # 新增：记录它在这一圈里排老几
        
        btn.setStyleSheet(f"""
            QPushButton {{
                background-color: #777777; 
                border-radius: {self.btn_size // 2}px;
                border: 1px solid #555;
                font-size: 10px;
                color: transparent; 
            }}
            QPushButton:checked {{
                background-color: #00FF00;
                border: 2px solid #FFFFFF;
                color: black;
            }}
            QPushButton:hover {{ border: 2px solid white; }}
        """)
        
        btn.setToolTip(f"ID: {led_id} (R{ring_index}-{intra_index})")
        self.led_buttons.append(btn)
        btn.show()

    def set_ring_state(self, is_select_action):
        """
        处理圆环选择逻辑
        is_select_action: True (应用选择), False (清除该圈)
        """
        target_ring_index = self.combo_rings.currentIndex()
        interval = self.spin_interval.value() # 获取间隔数
        
        # 计算步长: 间隔0->步长1(每1个选1个), 间隔1->步长2(每2个选1个)...
        step = interval + 1

        # 找出所有属于该圈的按钮
        # 这里的顺序即为生成时的顺序，也就是顺时针顺序
        target_buttons = [btn for btn in self.led_buttons if btn.property("ring_index") == target_ring_index]
        
        for btn in target_buttons:
            btn.blockSignals(True)
            
            if not is_select_action:
                # 如果是“清除该圈”，直接灭掉
                btn.setChecked(False)
            else:
                # 如果是“应用选择”，根据间隔逻辑判断
                intra_idx = btn.property("intra_index")
                
                # 只有当 圈内序号 能被 步长 整除时选中
                if intra_idx % step == 0:
                    btn.setChecked(True)
                else:
                    # 关键：如果不符合间隔，强制设为 False。
                    # 这样如果之前全亮，点击间隔1后，会变成隔一个亮一个。
                    btn.setChecked(False)
                    
            btn.blockSignals(False)

    def clear_all_leds(self):
        for btn in self.led_buttons:
            btn.blockSignals(True)
            btn.setChecked(False)
            btn.blockSignals(False)

    def export_leds_pickle(self):
        selected_ids = []
        for btn in self.led_buttons:
            if btn.isChecked():
                selected_ids.append(btn.property("led_id"))
        
        data_to_save = tuple(selected_ids)
        
        options = QFileDialog.Options()
        file_name, _ = QFileDialog.getSaveFileName(
            self, 
            "保存 LED 配置", 
            "led_pattern.pkl", 
            "Pickle Files (*.pkl);;All Files (*)", 
            options=options
        )
        
        if file_name:
            try:
                with open(file_name, 'wb') as f:
                    pickle.dump(data_to_save, f)
                print(f"成功保存 {len(data_to_save)} 个 LED 配置到: {file_name}")
            except Exception as e:
                QMessageBox.critical(self, "错误", f"保存失败:\n{str(e)}")

if __name__ == '__main__':
    app = QApplication(sys.argv)
    ex = LED_Selector()
    ex.show()
    sys.exit(app.exec_())