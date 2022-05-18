from PyQt5.QtWidgets import QWidget, QGridLayout, QLabel, QLineEdit, QComboBox, QFrame
from PyQt5.QtGui import QFont

from ophyd import EpicsSignalRO
from ophyd import Device as OphydDevice
from ophyd.signal import SignalRO

from bluesky_handling import EpicsFieldSignalRO

from main_classes import measurement_channel


class Device:
    """general class for all devices
    Arguments:
        - name: represents the device, should be unique
        - virtual: whether the device does not need any hardware
        - tags: list of strings for the device search
        - directory: usually the same as name, but also necessary to find the imported module
        - ophyd_device: used for initialisation of the channels, the class used for the bluesky-integration

    The subclasses of this class should all be called "subclass", they are imported via importlib in that way.
    Any derived device should also provide the name of its ophyd-class as a string self.ophyd_class_name
    """
    def __init__(self, name='', virtual=False, tags=None, files=None, directory='', requirements='', ophyd_device=None, ophyd_class_name=''):
        self.__save_dict__ = {}
        self.connection = Device_Connection()
        self.name = name
        self.virtual = virtual
        self.tags = [] if tags is None else tags
        self.files = [] if files is None else files
        self.directory = directory
        self.requirements = requirements
        self.settings = {}
        self.config = {}
        self.channels = {}
        self.ophyd_class_name = ophyd_class_name
        if ophyd_device is None:
            ophyd_device = OphydDevice
        # self.ophyd_device = ophyd_device
        ophyd_instance = ophyd_device(name='test')
        outputs = get_outputs(ophyd_instance)
        channels = {}
        if not channels:
            for chan in get_channels(ophyd_instance):
                is_out = chan in outputs
                channel = measurement_channel.Measurement_Channel(name=f'{self.name}.{chan}', output=is_out, device=self.name)
                self.channels.update({f'{self.name}_{chan}': channel})
        else:
            self.channels = channels
        for comp in ophyd_instance.walk_components():
            name = comp.item.attr
            cls = comp.item.cls
            if name in ophyd_instance.configuration_attrs and check_output(cls):
                self.config.update({f'{name}': 0})

    def get_config(self):
        return self.config

    def get_settings(self):
        return self.settings

    def set_connection(self, connection):
        self.connection = connection

    def get_channels(self):
        return self.channels

    def get_additional_string(self):
        return ''

    def get_special_steps(self):
        return {}
    # def read_channels(self, channels, use_set, n_tabs=1):
    #     tabs = '\t' * n_tabs
    #     prot_string = ''
    #     for i, channel in enumerate(channels):
    #         prot_string += f'{tabs}print("reading {channel} with use_set={use_set[i]}")\n'
    #     return prot_string
    #
    # def set_channels(self, channels, values):
    #     pass
    #
    # def init(self):
    #     pass
    #
    # def setup(self):
    #     pass
    #
    # def close(self):
    #     pass

def check_output(cls):
    output = not issubclass(cls, EpicsSignalRO)
    output = output and not issubclass(cls, EpicsFieldSignalRO)
    output = output and not issubclass(cls, SignalRO)
    return output

def get_outputs(dev:OphydDevice):
    """walks through the components of an ophyd-device and checks whether they can be written"""
    outputs = []
    for comp in dev.walk_components():
        cls = comp.item.cls
        name = comp.item.attr
        if check_output(cls):
            outputs.append(name)
    return outputs

def get_channels(dev:OphydDevice):
    """returns the components of an ophyd-device that are not listed in the configuration"""
    channels = []
    for comp in dev.walk_components():
        name = comp.item.attr
        if name not in dev.configuration_attrs:
            channels.append(name)
    return channels


class Device_Connection:
    def __init__(self, connection_type=None, **kwargs):
        self.__save_dict__ = {}
        self.connection_type = connection_type
        if connection_type == 'prologix-GPIB':
            self.IP_address = kwargs['IP_address']
            self.GPIB_address = kwargs['GPIB_address']


class Device_Config(QWidget):
    """Parent class for the configuration-widgets (shown on the frontpanel) of the devices.
    Arguments:
        - parent: handed to QWidget, usually the MainApp.
        - device_name: name of the device for the title of the widget.
        - data: data from the treeView_devices. It is needed to connect the settings to the correct device.
        - settings_dict: all the current settings of the device."""
    def __init__(self, parent=None, device_name='', data='', settings_dict=None, config_dict=None):
        super().__init__(parent)
        if settings_dict is None:
            settings_dict = {}
        if config_dict is None:
            config_dict = {}
        self.data = data

        layout = QGridLayout()
        self.setLayout(layout)

        label_title = QLabel(f'{device_name} - Configuration')
        title_font = QFont('MS Shell Dlg 2', 10)
        title_font.setWeight(QFont.Bold)
        label_title.setFont(title_font)
        self.label_custom_name = QLabel('Custom name:')
        self.label_connection = QLabel('Connection-type:')
        self.lineEdit_custom_name = QLineEdit(device_name)
        self.comboBox_connection_type = QComboBox()
        self.connector = Connection_Config()
        self.line_2 = QFrame(self)
        self.line_2.setFrameShape(QFrame.HLine)
        self.line_2.setFrameShadow(QFrame.Sunken)
        self.line_2.setObjectName("line_2")
        layout.addWidget(label_title, 0, 0, 1, 2)
        layout.addWidget(self.label_custom_name, 1, 0)
        layout.addWidget(self.lineEdit_custom_name, 1, 1)
        layout.addWidget(self.line_2, 2, 0, 1, 2)
        layout.addWidget(self.label_connection, 5, 0)
        layout.addWidget(self.comboBox_connection_type, 5, 1)
        self.settings_dict = settings_dict
        self.config_dict = config_dict
        self.comboBox_connection_type.currentTextChanged.connect(self.connection_type_changed)

    def connection_type_changed(self):
        """Called when the comboBox_connection_type is changed. Switches to another connector-widget to specify things like the Address of the device."""
        if self.comboBox_connection_type.currentText() == 'prologix-GPIB':
            self.connector = Prologix_Config()
            self.layout().addWidget(self.connector, 6, 0, 1, 2)

    def get_settings(self):
        """Updates the settings_dict with the current settings.
        Overwrite this function for each device to specify the settings. It is recommended to still call the parent for the connection-settings."""
        self.settings_dict.update({'connection': {'type': self.comboBox_connection_type.currentText()}})
        self.settings_dict['connection'].update(self.connector.get_settings())
        return self.settings_dict

    def load_settings(self):
        """Loads the settings from the settings_dict. Depending on the connection-type, the correct widget is set and the settings entered.
        Overwrite this function (and call it) for the specific settings."""
        if 'connection' in self.settings_dict:
            self.comboBox_connection_type.setCurrentText(self.settings_dict['connection']['type'])
            self.connector.load_settings(self.settings_dict['connection'])

    def get_config(self):
        return self.config_dict


class Connection_Config(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        layout = QGridLayout()
        self.setLayout(layout)

    def get_settings(self):
        return {}

    def load_settings(self, settings_dict):
        pass



class Prologix_Config(Connection_Config):
    """Widget for the settings when the connection is via a Prologix GPIB-Ethernet adapter."""
    def __init__(self, parent=None):
        super().__init__(parent)
        layout = self.layout()
        label_ip = QLabel('IP-Address:')
        label_GPIB = QLabel('GPIB-Address:')
        self.lineEdit_ip = QLineEdit()
        self.lineEdit_GPIB = QLineEdit()

        layout.addWidget(label_ip, 0, 0)
        layout.addWidget(label_GPIB, 1, 0)
        layout.addWidget(self.lineEdit_ip, 0, 1)
        layout.addWidget(self.lineEdit_GPIB, 1, 1)

    def get_settings(self):
        """Returns the set IP-Address and GPIB-Address."""
        return {'IP-Address': self.lineEdit_ip.text(),
                'GPIB-Address': self.lineEdit_GPIB.text()}

    def load_settings(self, settings_dict):
        """Loads the settings_dict, specifically the IP-Address and the GPIB-Address."""
        if 'IP-Address' in settings_dict:
            self.lineEdit_ip.setText(settings_dict['IP-Address'])
        if 'GPIB-Address' in settings_dict:
            self.lineEdit_GPIB.setText(settings_dict['GPIB-Address'])
