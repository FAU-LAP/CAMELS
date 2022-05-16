import os.path
import subprocess
import pandas as pd
import copy

from main_classes.protocol_class import Measurement_Protocol
from utility import variables_handling

standard_string = 'import numpy as np\n'
# standard_string += 'from ophyd.signal import EpicsSignal, EpicsSignalRO\n'
standard_string += 'from bluesky import RunEngine\n'
standard_string += 'from bluesky.callbacks.best_effort import BestEffortCallback\n'
standard_string += 'import bluesky.plan_stubs as bps\n'
# standard_string += 'from bluesky.utils import install_kicker\n'
standard_string += 'import databroker\n'
standard_string += 'from bluesky_widgets.qt.threading import wait_for_workers_to_quit\n'
standard_string += 'from PyQt5.QtWidgets import QApplication\n'
standard_string += 'from PyQt5.QtCore import QCoreApplication\n'
standard_string += 'from epics import caput\n'
standard_string += 'import datetime\n'
standard_string += 'from main_classes import plot_widget\n'
standard_string += 'from utility.databroker_export import broker_to_hdf5\n'

standard_run_string = '\n\n\nif __name__ == "__main__":\n'
standard_run_string += '\tRE = RunEngine()\n'
standard_run_string += '\tbec = BestEffortCallback()\n'
standard_run_string += '\tRE.subscribe(bec)\n'
standard_run_string += '\tapp = QCoreApplication.instance()\n'
standard_run_string += '\tif app is None:\n'
standard_run_string += '\t\tapp = QApplication(sys.argv)\n'
standard_run_string += '\tapp.aboutToQuit.connect(wait_for_workers_to_quit)\n'
standard_run_string += '\tif "--darkmode" in sys.argv:\n'
standard_run_string += '\t\tplot_widget.activate_dark_mode()\n'
standard_run_string += '\t\timport qdarkstyle\n'
standard_run_string += '\t\tapp.setStyleSheet(qdarkstyle.load_stylesheet_pyqt5())\n'
standard_run_string += '\t\tapp.setStyleSheet(qdarkstyle.load_stylesheet(qt_api="pyqt5"))\n'


def build_protocol(protocol:Measurement_Protocol, file_path, save_path='test.h5', catalog='CATALOG_NAME', userdata=None, sampledata=None):
    device_import_string = '\n'
    devices_string = '\n\tdevs = {}\n\tdevice_config = {}\n'
    variable_string = ''
    additional_string_devices = ''
    for var, val in variables_handling.protocol_variables.items():
        if variables_handling.check_data_type(val) == 'String':
            val = f'"{val}"'
        variable_string += f'{var} = {val}\n'
    for dev in protocol.get_used_devices():
        print(variables_handling.devices)
        device = variables_handling.devices[dev]
        classname = device.ophyd_class_name
        config = copy.deepcopy(device.get_config())
        settings = copy.deepcopy(device.get_settings())
        if 'connection' in settings:
            settings.pop('connection')
        if 'idn' in settings:
            settings.pop('idn')
        devices_string += f'\tsettings = {settings}\n'
        devices_string += f'\t{dev} = {classname}("{variables_handling.dev_preset}:{dev}:", name="{dev}", **settings)\n'
        devices_string += f'\tprint("connecting {dev}")\n'
        devices_string += f'\t{dev}.wait_for_connection()\n'
        devices_string += f'\tconfig = {config}\n'
        devices_string += f'\tconfigs = {dev}.configure(config)[1]\n'
        devices_string += f'\tdevice_config["{dev}"] = {{}}\n'
        devices_string += f'\tdevice_config["{dev}"].update(configs)\n'
        devices_string += f'\tdevice_config["{dev}"]["settings"] = settings\n'
        devices_string += f'\tdevs.update({{"{dev}": {dev}}})\n'
        device_import_string += f'from {dev}.{dev}_ophyd import {classname}\n'
        additional_string_devices += device.get_additional_string()
    devices_string += '\tprint("devices connected")\n'
    devices_string += '\tmd = {"device_config": device_config}\n'
    plot_string = '\n'
    for i, plot in pd.DataFrame(protocol.plots).iterrows():
        plot_string += f'\tplot_{i} = plot_widget.PlotWidget(run_engine=RE, x_name="{plot["X-axis"]}", y_names={plot["Y-axes"]}, ylabel="{plot["y-label"]}", xlabel="{plot["x-label"]}", title="{plot["title"]}")\n'
        plot_string += f'\tplot_{i}.show()\n'
    plot_string += '\n'
    # for device in protocol.get_used_devices():
    #     print(device)
    protocol_string = 'import sys\n'
    protocol_string += f'sys.path.append(r"{variables_handling.CAMELS_path}")\n'
    protocol_string += f'sys.path.append("{variables_handling.device_driver_path}")\n\n'
    protocol_string += standard_string
    protocol_string += f'{variable_string}\n\n'
    protocol_string += device_import_string
    protocol_string += protocol.get_plan_string()
    protocol_string += standard_run_string
    protocol_string += f'\tcatalog = databroker.catalog["{catalog}"]\n'
    protocol_string += '\tRE.subscribe(catalog.v1.insert)\n\n'
    protocol_string += devices_string
    protocol_string += additional_string_devices
    protocol_string += plot_string
    protocol_string += user_sample_string(userdata, sampledata)
    protocol_string += f'\tuids = RE({protocol.name}_plan(devs, md=md))\n'

    standard_save_string = '\n\n\truns = catalog[uids]\n'
    standard_save_string += f'\tbroker_to_hdf5(runs, "{save_path}")\n\n\n'
    standard_save_string += '\tsys.exit(app.exec_())\n'

    protocol_string += standard_save_string
    if not os.path.isdir(os.path.dirname(file_path)):
        os.makedirs(os.path.dirname(file_path))
    with open(file_path, 'w+') as file:
        file.write(protocol_string)

def user_sample_string(userdata, sampledata):
    u_s_string = f'\tmd["user"] = {userdata}\n'
    u_s_string += f'\tmd["sample"] = {sampledata}\n'
    return u_s_string

def run_protocol(protocol:Measurement_Protocol, file_path, sig_step=None, info_step=None):
    if sig_step is not None:
        sig_step.emit(0)
    total_time = 1
    for step in protocol.loop_steps:
        total_time += step.time_weight
    args = []
    if variables_handling.dark_mode:
        args.append('--darkmode')
    p = subprocess.Popen(['python', file_path] + args, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, bufsize=1)
    i = 1
    for line in iter(p.stdout.readline, b''):
        text = line.decode().rstrip()
        if text.startswith("starting loop_step "):
            if sig_step is not None:
                sig_step.emit(int(i/total_time * 100))
            i += 1
        elif text.startswith("protocol finished!"):
            if sig_step is not None:
                sig_step.emit(100)
                break
        else:
            if info_step is None:
                print(text)
            else:
                info_step.emit(text)
    # if info_step is not None:
    #     info_step.emit('\n\n')
    # for line in p.stderr.readlines():
    #     text = line.decode().rstrip()
    #     if info_step is None:
    #         print(text)
    #     else:
    #         info_step.emit(text)
    if info_step is not None:
        info_step.emit('\n\n\n')
    if sig_step is not None:
        sig_step.emit(100)
