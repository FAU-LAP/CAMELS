from PyQt5.QtCore import QThread, pyqtSignal

from EPICS_handling import make_ioc

class Make_Ioc(QThread):
    sig_step = pyqtSignal(int)
    info_step = pyqtSignal(str)

    def __init__(self, ioc_name='Default', device_data=None):
        if device_data is None:
            device_data = {}
        super(Make_Ioc, self).__init__()
        self.ioc_name = ioc_name
        self.device_data = device_data

    def run(self):
        self.sig_step.emit(0)
        info = make_ioc.clean_up_ioc(self.ioc_name)
        self.info_step.emit(info)
        self.sig_step.emit(1)
        info = make_ioc.change_devices(self.device_data, self.ioc_name)
        self.info_step.emit(info)
        self.sig_step.emit(10)
        info = make_ioc.make_ioc(self.ioc_name)
        self.info_step.emit(info)
        self.sig_step.emit(100)