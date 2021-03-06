import serial.tools.list_ports

from PyQt5.QtWidgets import QWidget, QGridLayout, QLabel, QLineEdit, QComboBox,\
    QFrame, QCheckBox
from PyQt5.QtGui import QFont
from PyQt5.QtCore import pyqtSignal, Qt

from ophyd import EpicsSignalRO
from ophyd import Device as OphydDevice
from ophyd.signal import SignalRO

from bluesky_handling import EpicsFieldSignalRO

from main_classes.measurement_channel import Measurement_Channel


class Device:
    """General class for all devices

    The subclasses of this class should all be called "subclass", they
    are imported via importlib in that way.
    Any derived device should also provide the name of its ophyd-class
    as a string self.ophyd_class_name.

    Attributes
    ----------
    name : str
        represents the device, should be unique
    virtual : bool
        whether the device does not need any hardware
    tags : list
        list of strings for the device search
    files : list
        list of the filenames that are necessary for the IOC
        The files should be in the same directory
    directory : str
        usually the same as name, but also necessary to find the
        imported module
    requirements : list
        list of additional modules needed for the IOC (e.g. Prologix)
    ophyd_class_name : str
        name of the class of ophyd_device
    ioc_settings : dict
        the settings used when building the IOC  # TODO move out of settings
    settings : dict
        settings handed to the ophyd class at runtime of the protocol
    config : dict
        values, the config-attributes should be set to
    channels : dict
        channels of the device (i.e.: Signals that are not config)
    """

    def __init__(self, name='', virtual=False, tags=None, files=None,
                 directory='', requirements=None, ophyd_device=None,
                 ophyd_class_name=''):
        """
        Parameters
        ----------
        name : str
            represents the device, should be unique
        virtual : bool
            whether the device does not need any hardware
        tags : list
            list of strings for the device search
        files : list
            list of the filenames that are necessary for the IOC
            The files should be in the same directory
        directory : str
            usually the same as name, but also necessary to find the
            imported module
        requirements : list
            list of additional modules needed for the IOC (e.g. Prologix)
        ophyd_device : ophyd.Device
            used for initialisation of the channels, the class used for
            the bluesky-integration
        ophyd_class_name : str
            name of the class of ophyd_device
        """

        self.__save_dict__ = {}  # TODO use or remove
        self.connection = Device_Connection()  # TODO use or remove
        self.name = name
        self.custom_name = name
        self.virtual = virtual
        self.tags = [] if tags is None else tags
        self.files = [] if files is None else files
        self.directory = directory
        self.requirements = requirements
        self.ioc_settings = {}  # TODO usage thereof, make it distinguish more clear
        self.settings = {}
        self.config = {}
        self.passive_config = {}
        self.channels = {}
        self.ophyd_class_name = ophyd_class_name
        if ophyd_device is None:
            ophyd_device = OphydDevice
        # self.ophyd_device = ophyd_device
        self.ophyd_instance = ophyd_device(name='test')
        outputs = get_outputs(self.ophyd_instance)
        for chan in get_channels(self.ophyd_instance):
            is_out = chan in outputs
            channel = Measurement_Channel(name=f'{self.custom_name}.{chan}',
                                          output=is_out,device=self.custom_name)
            self.channels.update({f'{self.custom_name}_{chan}': channel})
        for comp in self.ophyd_instance.walk_components():
            name = comp.item.attr
            cls = comp.item.cls
            if name in self.ophyd_instance.configuration_attrs:
                if check_output(cls):
                    self.config.update({f'{name}': 0})
                else:
                    self.passive_config.update({f'{name}': 0})

    def get_finalize_steps(self):
        return ''

    def get_passive_config(self):
        return self.passive_config

    def get_config(self):
        """returns self.config, should be overwritten for special
        purposes (e.g. leaving out some keys of the dictionary)"""
        return self.config

    def get_settings(self):
        """returns self.settings, should be overwritten for special
        purposes (e.g. leaving out some keys of the dictionary)"""
        return self.settings

    def get_ioc_settings(self):
        """returns self.ioc_settings, should be overwritten for special
        purposes (e.g. leaving out some keys of the dictionary)"""
        return self.ioc_settings

    def get_substitutions_string(self, ioc_name:str, communication:str):
        substring = f'file "db/{self.name}.db" {{\n'
        substring += f'    {{SETUP = "{ioc_name}", device = "{self.custom_name}", COMM = "{communication}"}}\n'
        substring += '}'
        return substring

    def get_channels(self):
        """returns self.channels, should be overwritten for special
        purposes (e.g. leaving out some keys of the dictionary)"""
        self.channels = {}
        outputs = get_outputs(self.ophyd_instance)
        for chan in get_channels(self.ophyd_instance):
            is_out = chan in outputs
            channel = Measurement_Channel(name=f'{self.custom_name}.{chan}',
                                          output=is_out,device=self.custom_name)
            self.channels.update({f'{self.custom_name}_{chan}': channel})
        return self.channels

    def get_additional_string(self):
        """returns a string that will be added into the protocol after
        connecting to the device."""
        return ''

    def get_special_steps(self):
        """returns a dictionary containing containing device-specific
        loopsteps. The key is the loopstep's name, the value a list
        containing the Class of the step, and its config-widget."""
        return {}

def check_output(cls) -> bool:
    """Returns False if the give `cls` is an instance of a read-only Signal."""
    output = not issubclass(cls, EpicsSignalRO)
    output = output and not issubclass(cls, EpicsFieldSignalRO)
    output = output and not issubclass(cls, SignalRO)
    return output

def get_outputs(dev:OphydDevice):
    """walks through the components of an ophyd-device and checks
    whether they can be written"""
    outputs = []
    for comp in dev.walk_components():
        cls = comp.item.cls
        name = comp.item.attr
        if check_output(cls):
            outputs.append(name)
    return outputs

def get_channels(dev:OphydDevice):
    """returns the components of an ophyd-device that are not listed in
    the configuration"""
    channels = []
    for comp in dev.walk_components():
        name = comp.item.attr
        if name not in dev.configuration_attrs:
            channels.append(name)
    return channels


class Device_Connection:  # TODO use or remove
    def __init__(self, connection_type=None, **kwargs):
        self.__save_dict__ = {}
        self.connection_type = connection_type
        if connection_type == 'prologix-GPIB':
            self.IP_address = kwargs['IP_address']
            self.GPIB_address = kwargs['GPIB_address']


class Device_Config(QWidget):
    """Parent class for the configuration-widgets
    (shown on the frontpanel) of the devices."""
    ioc_change = pyqtSignal()
    name_change = pyqtSignal(str)

    def __init__(self, parent=None, device_name='', data='', settings_dict=None,
                 config_dict=None, ioc_settings=None):
        """
        Parameters
        ----------
        parent : QWidget
            handed to QWidget, usually the MainApp
        device_name : str
            name of the device for the title of the widget
        data : str
            data from the treeView_devices, it is needed to connect the
            settings to the correct device
        settings_dict : dict
            all the current settings of the device
        config_dict : dict
            the current configuration of the device
        ioc_settings : dict
            the ioc-specific settings of the device
        """

        super().__init__(parent)
        if settings_dict is None:
            settings_dict = {}
        if config_dict is None:
            config_dict = {}
        if ioc_settings is None:
            ioc_settings = {}
        self.data = data

        layout = QGridLayout()
        self.setLayout(layout)

        label_title = QLabel(f'{device_name} - Configuration')
        title_font = QFont('MS Shell Dlg 2', 10)
        title_font.setWeight(QFont.Bold)
        label_title.setFont(title_font)

        self.label_custom_name = QLabel('Custom name:')
        self.label_connection = QLabel('Connection-type:')
        self.lineEdit_custom_name = QLineEdit(data)
        self.checkBox_use_local_ioc = QCheckBox('Use local IOC')
        self.checkBox_use_local_ioc.setChecked(True)
        loc = True
        if 'use_local_ioc' in ioc_settings:
            loc = ioc_settings['use_local_ioc']
            self.checkBox_use_local_ioc.setChecked(loc)
        self.label_ioc_name = QLabel('IOC name:')
        self.label_ioc_name.setAlignment(Qt.AlignRight)
        self.lineEdit_ioc_name = QLineEdit()
        if 'ioc_name' in ioc_settings:
            self.lineEdit_ioc_name.setText(ioc_settings['ioc_name'])
        self.label_ioc_name.setEnabled(not loc)
        self.lineEdit_ioc_name.setEnabled(not loc)
        self.comboBox_connection_type = QComboBox()
        self.connector = Connection_Config()

        self.line_2 = QFrame(self)
        self.line_2.setFrameShape(QFrame.HLine)
        self.line_2.setFrameShadow(QFrame.Sunken)
        self.line_2.setObjectName("line_2")

        layout.addWidget(label_title, 0, 0, 1, 5)
        layout.addWidget(self.label_custom_name, 1, 0)
        layout.addWidget(self.lineEdit_custom_name, 1, 1, 1, 2)
        layout.addWidget(self.checkBox_use_local_ioc, 2, 0)
        layout.addWidget(self.label_ioc_name, 2, 1)
        layout.addWidget(self.lineEdit_ioc_name, 2, 2)
        layout.addWidget(self.line_2, 3, 0, 1, 5)
        layout.addWidget(self.label_connection, 5, 0)
        layout.addWidget(self.comboBox_connection_type, 5, 1, 1, 2)

        self.settings_dict = settings_dict
        self.config_dict = config_dict
        self.ioc_settings = ioc_settings
        self.comboBox_connection_type.currentTextChanged.connect(self.connection_type_changed)
        self.lineEdit_custom_name.textChanged.connect(lambda x: self.name_change.emit(x))
        self.checkBox_use_local_ioc.clicked.connect(self.ioc_set_changed)

    def ioc_set_changed(self):
        loc = self.checkBox_use_local_ioc.isChecked()
        self.label_ioc_name.setEnabled(not loc)
        self.lineEdit_ioc_name.setEnabled(not loc)
        self.ioc_change.emit()


    def connection_type_changed(self):
        """Called when the comboBox_connection_type is changed. Switches
        to another connector-widget to specify things like the Address
        of the device."""
        if self.comboBox_connection_type.currentText() == 'prologix-GPIB':
            self.connector = Prologix_Config()
        elif self.comboBox_connection_type.currentText() == 'USB-serial':
            self.connector = USB_Serial_Config()
        self.layout().addWidget(self.connector, 6, 0, 1, 5)
        self.connector.connection_change.connect(self.ioc_change.emit)
        self.ioc_change.emit()

    def get_ioc_settings(self):
        self.ioc_settings.update({'use_local_ioc': self.checkBox_use_local_ioc.isChecked(),
                                  'ioc_name': self.lineEdit_ioc_name.text()})
        self.ioc_settings.update({'connection': {'type': self.comboBox_connection_type.currentText()}})
        self.ioc_settings['connection'].update(self.connector.get_settings())
        return self.ioc_settings

    def get_settings(self):
        """Updates the settings_dict with the current settings.
        Overwrite this function for each device to specify the settings.
        It is recommended to still call the super() method for the
        connection-settings."""
        self.settings_dict.update({'connection': {'type': self.comboBox_connection_type.currentText()}})
        self.settings_dict['connection'].update(self.connector.get_settings())
        return self.settings_dict

    def load_settings(self):
        """Loads the settings from the settings_dict. Depending on the
        connection-type, the correct widget is set and the settings
        entered. Overwrite this function (and call it) for the specific
        settings."""
        if 'connection' in self.ioc_settings:
            self.comboBox_connection_type.setCurrentText(self.ioc_settings['connection']['type'])
            self.connector.load_settings(self.ioc_settings['connection'])

    def get_config(self):
        """Returns the config_dict of the device. Overwrite this
        function for each device to specify the config."""
        return self.config_dict


class Device_Config_Sub(QWidget):
    def __init__(self, settings_dict=None, parent=None, config_dict=None):
        super().__init__(parent)
        self.settings_dict = settings_dict or {}
        self.config_dict = config_dict or {}
        if settings_dict is None and config_dict is None:
            self.setLayout(QGridLayout())
            self.layout().addWidget(QLabel('Nothing to configure!'))

    def get_config(self):
        return self.config_dict

    def get_settings(self):
        return self.settings_dict


class Connection_Config(QWidget):
    """Base Class for the widgets used to specify the connection of a
    given device."""
    connection_change = pyqtSignal()

    def __init__(self, parent=None):
        super().__init__(parent)
        layout = QGridLayout()
        layout.setContentsMargins(0, 0, 0, 0)
        self.setLayout(layout)

    def get_settings(self):
        """Overwrite to return the connection-specific settings"""
        return {}

    def load_settings(self, settings_dict):
        """Overwrite to load the connection-specific settings from
        `settings_dict`."""
        pass



class Prologix_Config(Connection_Config):
    """Widget for the settings when the connection is via a Prologix
    GPIB-Ethernet adapter."""
    def __init__(self, parent=None):
        super().__init__(parent)
        layout = self.layout()
        label_ip = QLabel('IP-Address:')
        label_GPIB = QLabel('GPIB-Address:')
        self.lineEdit_ip = QLineEdit()
        self.lineEdit_GPIB = QLineEdit()
        self.lineEdit_GPIB.textChanged.connect(self.connection_change.emit)
        self.lineEdit_ip.textChanged.connect(self.connection_change.emit)

        layout.addWidget(label_ip, 0, 0)
        layout.addWidget(label_GPIB, 1, 0)
        layout.addWidget(self.lineEdit_ip, 0, 1)
        layout.addWidget(self.lineEdit_GPIB, 1, 1)

    def get_settings(self):
        """Returns the set IP-Address and GPIB-Address."""
        return {'IP-Address': self.lineEdit_ip.text(),
                'GPIB-Address': self.lineEdit_GPIB.text()}

    def load_settings(self, settings_dict):
        """Loads the settings_dict, specifically the IP-Address and the
        GPIB-Address."""
        if 'IP-Address' in settings_dict:
            self.lineEdit_ip.setText(settings_dict['IP-Address'])
        if 'GPIB-Address' in settings_dict:
            self.lineEdit_GPIB.setText(settings_dict['GPIB-Address'])


class USB_Serial_Config(Connection_Config):
    def __init__(self, parent=None):
        super().__init__(parent)
        label_port = QLabel('COM-Port:')
        self.comboBox_port = QComboBox()
        self.ports = get_ports()
        self.comboBox_port.addItems(self.ports.keys())
        self.comboBox_port.currentTextChanged.connect(self.change_desc)

        self.label_desc = QLabel()
        self.label_desc.setEnabled(False)
        self.label_hwid = QLabel()
        self.label_hwid.setEnabled(False)

        self.layout().addWidget(label_port, 0, 0)
        self.layout().addWidget(self.comboBox_port, 0, 1, 1, 4)
        self.layout().addWidget(self.label_desc, 1, 0, 1, 2)
        self.layout().addWidget(self.label_hwid, 1, 2, 1, 3)
        self.change_desc()

    def change_desc(self):
        port = self.comboBox_port.currentText()
        desc = self.ports[port]['description']
        hwid = self.ports[port]['hardware']
        self.label_desc.setText(desc)
        self.label_hwid.setText(hwid)

    def get_settings(self):
        return {'Port': self.comboBox_port.currentText()}

    def load_settings(self, settings_dict):
        if 'Port' in settings_dict and settings_dict['Port'] in self.ports.keys():
            self.comboBox_port.setCurrentText(settings_dict['Port'])



def get_ports():
    ports = serial.tools.list_ports.comports()
    port_dict = {}
    for port, desc, hwid in sorted(ports):
        port_dict[port] = {'description': desc, 'hardware': hwid}
    return port_dict

