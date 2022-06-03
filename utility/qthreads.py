from PyQt5.QtCore import QThread, pyqtSignal

import subprocess

from EPICS_handling import make_ioc
from bluesky_handling import protocol_builder


class Make_Ioc(QThread):
    """Called from the MainApp.
    It runs the steps from the make_ioc package to create a
    fully operational IOC."""
    sig_step = pyqtSignal(int)
    info_step = pyqtSignal(str)

    def __init__(self, ioc_name='Default', device_data=None):
        """

        Parameters
        ----------
        ioc_name : str, default "Default"
            The name of the IOC. When calling from the function in
            MainApp, it is the name of the device-preset.
        device_data : dict, default None
            The data-dictionary for the devices (including settings etc.)
        """
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
        info = make_ioc.make_ioc(self.ioc_name, self.info_step, self.sig_step)
        # self.info_step.emit(info)
        self.sig_step.emit(100)


class Run_Protocol(QThread):
    """Runs the given protocol with a file at the given path."""
    sig_step = pyqtSignal(int)
    info_step = pyqtSignal(str)

    def __init__(self, protocol, path):
        super().__init__()
        self.protocol = protocol
        self.path = path

    def run(self) -> None:
        protocol_builder.run_protocol(self.protocol, self.path, self.sig_step,
                                      self.info_step)

class Run_IOC(QThread):
    """Runs the given IOC in the background."""
    info_step = pyqtSignal(str)

    def __init__(self, ioc_name='Default'):
        super().__init__()
        self.ioc_name = ioc_name
        self.popen = None
        self.last_inputs = []
        self.curr_last = -1

    def run(self):
        self.popen = subprocess.Popen(['wsl', './EPICS_handling/run_ioc.cmd',
                                       self.ioc_name],
                                      stdout=subprocess.PIPE,
                                      stderr=subprocess.STDOUT,
                                      stdin=subprocess.PIPE, bufsize=1)
        for line in iter(self.popen.stdout.readline, b''):
            text = line.decode().rstrip()
            self.info_step.emit(text)
        # while True:
        #     line = self.popen.stdout.readline()
        #     text = line.decode().rstrip()
        #     self.info_step.emit(text)

    def write_to_ioc(self, msg):
        if 'exit' in msg:
            raise Exception('Please stop the IOC only using the button!\n(The command "exit" is not allowed!)')
        self.last_inputs.append(msg)
        if self.popen is not None:
            self.popen.stdin.write(bytes(f'{msg}\n', 'utf-8'))
            self.popen.stdin.flush()


    def terminate(self) -> None:
        if self.popen is not None:
            self.popen.communicate(input=b'exit')
        super().terminate()
