from PyQt5.QtWidgets import QWidget, QTableWidgetItem, QLabel, QGridLayout

from main_classes.loop_step import Loop_Step_Config, Loop_Step
from utility.variable_tool_tip_box import Variable_Box

class Wait_Loop_Step(Loop_Step):
    def __init__(self, name='', parent_step=None, step_info=None, **kwargs):
        super().__init__(name, parent_step, **kwargs)
        self.step_type = 'Wait'
        if step_info is None:
            step_info = {}
        self.wait_time = step_info['wait_time'] if 'wait_time' in step_info else 0

    def get_protocol_string(self, n_tabs=1):
        tabs = '\t' * n_tabs
        protocol_string = f'{tabs}print("starting loop_step {self.full_name}")\n'
        protocol_string += f'{tabs}yield from bps.sleep({self.wait_time})\n'
        return protocol_string


class Wait_Loop_Step_Config(Loop_Step_Config):
    def __init__(self, loop_step:Wait_Loop_Step, parent=None):
        super().__init__(parent, loop_step)
        self.sub_widget = Wait_Loop_Step_Config_Sub(loop_step, self)
        self.layout().addWidget(self.sub_widget, 1, 0)


class Wait_Loop_Step_Config_Sub(QWidget):
    def __init__(self, loop_step:Wait_Loop_Step, parent=None):
        super().__init__(parent)
        self.loop_step = loop_step

        label1 = QLabel('Wait for')
        label2 = QLabel('seconds')
        self.lineEdit_duration = Variable_Box(self)
        self.lineEdit_duration.setText(str(loop_step.wait_time))
        self.lineEdit_duration.textChanged.connect(self.update_duration)

        layout = QGridLayout()
        layout.setContentsMargins(0, 0, 0, 0)
        layout.addWidget(label1, 0, 0)
        layout.addWidget(self.lineEdit_duration, 0, 1)
        layout.addWidget(label2, 0, 2)
        self.setLayout(layout)

    def update_duration(self):
        self.loop_step.wait_time = self.lineEdit_duration.text()

