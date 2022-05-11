import json
import sys
import qdarkstyle
import importlib
import os

from copy import deepcopy

from PyQt5.QtCore import QCoreApplication, Qt, QItemSelectionModel
from PyQt5.QtWidgets import QApplication, QMainWindow, QFileDialog, QMessageBox, QWidget, QMenu, QAction, QToolButton, QUndoStack, QShortcut
from PyQt5.QtGui import QIcon, QCloseEvent, QStandardItem, QStandardItemModel, QMouseEvent

from utility import exception_hook, load_save_functions, treeView_functions, qthreads, drag_drop_tree_view, number_formatting, variables_handling, bluesky_handling

from gui.mainWindow import Ui_MainWindow

from frontpanels.device_add_dialog import AddDeviceDialog
from frontpanels.settings_window import Settings_Window
from main_classes.protocol_class import Measurement_Protocol, General_Protocol_Settings
from commands import change_sequence

from loop_steps import make_step_of_type

os.environ['QT_API'] = 'pyqt5'


class MainWindow(QMainWindow, Ui_MainWindow):
    """Main Window for the program. Connects to all the other classes."""
    def __init__(self, parent=None):
        # basic setup
        super(MainWindow, self).__init__(parent)
        self.setupUi(self)
        self.setWindowTitle('CAMELS - Configurable Application for Measurement- and Laboratory-Systems')
        self.setWindowIcon(QIcon('graphics/CAMELS.png'))
        predev, premeas = load_save_functions.get_preset_list()
        for pre in predev:
            self.comboBox_device_preset.addItem(pre)
        if not predev:
            self.comboBox_device_preset.addItem('Default')
        for pre in premeas:
            self.comboBox_measurement_preset.addItem(pre)
        if not premeas:
            self.comboBox_measurement_preset.addItem('Default')
        self.setStyleSheet("QSplitter::handle{background: gray;}")
        self.make_thread = None

        # devices
        self.active_devices_dict = {}
        variables_handling.devices = self.active_devices_dict
        self.lineEdit_device_search.returnPressed.connect(self.build_devices_tree)
        self.item_model_devices = QStandardItemModel(0,1)
        self.treeView_devices.setModel(self.item_model_devices)
        self.treeView_devices.setHeaderHidden(True)
        all_devices = QStandardItem('All devices')
        all_devices.setEditable(False)
        virtual_devices = QStandardItem('Virtual devices')
        virtual_devices.setEditable(False)
        by_tags = QStandardItem('Devices by tags')
        by_tags.setEditable(False)
        self.item_model_devices.appendRow(all_devices)
        self.item_model_devices.appendRow(virtual_devices)
        self.item_model_devices.appendRow(by_tags)
        self.textEdit_console_output.setHidden(True)
        self.textEdit_console_output_meas.setHidden(True)

        # measurements
        self.run_thread = None
        self.protocols_dict = {}
        self.item_model_protocols = QStandardItemModel(0,1)
        self.listView_protocols.setModel(self.item_model_protocols)
        self.item_model_sequence = QStandardItemModel(0,1)
        self.sequence_main_widget.layout().removeWidget(self.treeView_protocol_sequence)
        self.treeView_protocol_sequence.deleteLater()
        self.treeView_protocol_sequence = drag_drop_tree_view.Drag_Drop_TreeView()
        self.sequence_main_widget.layout().addWidget(self.treeView_protocol_sequence, 5, 0, 1, 3)
        self.treeView_protocol_sequence.setModel(self.item_model_sequence)
        self.treeView_protocol_sequence.customContextMenuRequested.connect(self.sequence_right_click)
        self.treeView_protocol_sequence.dragdrop.connect(self.update_loop_step_order)
        self.current_protocol = None
        self.loop_step_configuration_widget = None
        self.copied_loop_step = None
        self.sequence_main_widget.setEnabled(False)


        #connecting buttons
        self.pushButton_add_device.clicked.connect(self.add_device)
        self.pushButton_remove_device.clicked.connect(self.remove_device)
        self.actionSettings.triggered.connect(self.change_preferences)
        self.actionNew_Device_Preset.triggered.connect(self.new_device_preset)
        self.actionNew_Measurement_Preset.triggered.connect(self.new_measurement_preset)
        self.actionSave_Device_Preset.triggered.connect(self.save_device_state)
        self.actionSave_Measurement_Preset.triggered.connect(self.save_measurement_state)
        self.actionSave_Device_Preset_As.triggered.connect(self.save_device_preset_as)
        self.actionSave_Measurement_Preset_As.triggered.connect(self.save_measurement_preset_as)
        self.actionOpen_Backup_Device_Preset.triggered.connect(self.load_backup_device_preset)
        self.actionLoad_Backup_Measurement_Preset.triggered.connect(self.load_backup_measurement_preset)
        self.pushButton_make_EPICS_environment.clicked.connect(self.make_epics_environment)
        self.pushButton_show_console_output.clicked.connect(self.show_console_output)
        self.treeView_devices.clicked.connect(self.tree_click)

        self.pushButton_add_protocol.clicked.connect(self.add_protocol)
        self.pushButton_remove_protocol.clicked.connect(self.remove_protocol)
        self.item_model_protocols.itemChanged.connect(self.change_protocol_name)
        self.pushButton_show_output_meas.clicked.connect(self.show_meas_output)
        self.listView_protocols.clicked.connect(self.protocol_selected)
        self.pushButton_move_step_up.clicked.connect(lambda state: self.move_loop_step(-1,0))
        self.pushButton_move_step_down.clicked.connect(lambda state: self.move_loop_step(1,0))
        self.pushButton_move_step_in.clicked.connect(lambda state: self.move_loop_step(0,1))
        self.pushButton_move_step_out.clicked.connect(lambda state: self.move_loop_step(0,-1))
        self.treeView_protocol_sequence.clicked.connect(lambda x: self.tree_click_sequence(False))
        self.add_actions = []
        # for stp in sorted(drag_drop_tree_view.step_types, key=lambda x: x.lower()):
        for stp in sorted(make_step_of_type.step_type_config.keys(), key=lambda x: x.lower()):
            action = QAction(stp)
            action.triggered.connect(lambda state, x=stp: self.add_loop_step(x))
            self.add_actions.append(action)
        device_actions = []
        for stp in make_step_of_type.get_device_steps():
            action = QAction(stp)
            action.triggered.connect(lambda state, x=stp: self.add_loop_step(x))
            device_actions.append(action)
        self.toolButton_add_step.addActions(self.add_actions)
        if device_actions:
            self.toolButton_add_step.addActions(device_actions)
        self.toolButton_add_step.setPopupMode(QToolButton.InstantPopup)
        self.pushButton_remove_step.clicked.connect(lambda x: self.remove_loop_step(True))
        self.pushButton_show_protocol_settings.clicked.connect(lambda x: self.tree_click_sequence(True))
        self.pushButton_build_protocol.clicked.connect(self.build_current_protocol)
        self.pushButton_run_protocol.clicked.connect(self.run_current_protocol)


        # saving and loading
        self.__save_dict_devices__ = {}
        self.__save_dict_meas__ = {}
        self.saving = False
        self._current_device_preset = ['Default']
        self._current_measurement_preset = ['Default']
        self.device_save_dict = {'_current_device_preset': self._current_device_preset,
                                 'active_devices_dict': self.active_devices_dict,
                                 'lineEdit_device_search': self.lineEdit_device_search}
        self.meas_save_dict = {'_current_measurement_preset': self._current_measurement_preset,
                               'protocols_dict': self.protocols_dict}
        self.preferences = {}
        self.load_preferences()
        sys.path.append(self.preferences['device_driver_path'])
        self.load_state()
        self.device_config_widget = QWidget()
        self.comboBox_device_preset.currentTextChanged.connect(self.change_device_preset)
        self.comboBox_measurement_preset.currentTextChanged.connect(self.change_measurement_preset)

        self.inside_function = False
        self.undo_stack = QUndoStack(self)
        self.actionUndo.triggered.connect(self.undo)
        self.actionRedo.triggered.connect(self.redo)
        self.actionUndo.setEnabled(self.undo_stack.canUndo())
        self.actionRedo.setEnabled(self.undo_stack.canRedo())
        QShortcut('Ctrl+z', self).activated.connect(self.undo)
        QShortcut('Ctrl+y', self).activated.connect(self.redo)
        QShortcut('Ctrl+s', self).activated.connect(self.save_state)

    def mousePressEvent(self, a0: QMouseEvent) -> None:
        but = a0.button()
        if but == 8:
            self.undo()
        elif but == 16:
            self.redo()
        else:
            super().mousePressEvent(a0)

    def undo(self):
        self.undo_stack.undo()
        self.actionUndo.setEnabled(self.undo_stack.canUndo())
        self.actionRedo.setEnabled(self.undo_stack.canRedo())

    def redo(self):
        self.undo_stack.redo()
        self.actionUndo.setEnabled(self.undo_stack.canUndo())
        self.actionRedo.setEnabled(self.undo_stack.canRedo())

    # --------------------------------------------------
    # Overwriting parent-methods
    # --------------------------------------------------
    def close(self) -> bool:
        """Calling the save_state method when closing the window."""
        if self.preferences['autosave']:
            self.save_state()
        return super().close()

    def closeEvent(self, a0: QCloseEvent) -> None:
        """Calling the save_state method when closing the window."""
        if self.preferences['autosave']:
            self.save_state()
        super().closeEvent(a0)

    # --------------------------------------------------
    # save / load methods
    # --------------------------------------------------
    def load_preferences(self):
        """Loads the preferences.
        - autosave: turn on / off autosave on closing the program."""
        self.preferences = load_save_functions.get_preferences()
        number_formatting.preferences = self.preferences
        if 'dark_mode' in self.preferences:
            self.toggle_dark_mode()
        variables_handling.device_driver_path = self.preferences['device_driver_path']

    def toggle_dark_mode(self):
        dark = self.preferences['dark_mode']
        main_app = QApplication.instance()
        if main_app is None:
            raise RuntimeError("MainApp not found.")
        if dark:
            # file = QFile('graphics/dark.qss')
            # file.open(QFile.ReadOnly | QFile.Text)
            # stream = QTextStream(file)
            # main_app.setStyleSheet(stream.readAll())
            main_app.setStyleSheet(qdarkstyle.load_stylesheet_pyqt5())
            main_app.setStyleSheet(qdarkstyle.load_stylesheet(qt_api='pyqt5'))
            variables_handling.dark_mode = True
        else:
            main_app.setStyleSheet('')
            variables_handling.dark_mode = False


    def change_preferences(self):
        """Called when any preferences are changed. Makes the dictionary of preferences and calls save_preferences from the load_save_functions module."""
        settings_dialog = Settings_Window(parent=self, settings=self.preferences)
        if settings_dialog.exec_():
            self.preferences = settings_dialog.get_settings()
            number_formatting.preferences = self.preferences
            self.toggle_dark_mode()
            load_save_functions.save_preferences(self.preferences)
            variables_handling.device_driver_path = self.preferences['device_driver_path']
        # prefs = {'autosave': self.actionAutosave_on_closing.isChecked(),
        #          'dark_mode': self.actionDark_Mode.isChecked()}
        # load_save_functions.save_preferences(prefs)

    def save_state(self):
        """Saves the current states of both presets."""
        self.save_device_state()
        self.save_measurement_state()
        print('current state saved!')

    def save_device_state(self):
        """makes the __save_dict_devices__, then calls the autosave."""
        self.make_device_save_dict()
        load_save_functions.autosave_preset(self._current_device_preset[0], self.__save_dict_devices__)

    def save_measurement_state(self):
        """makes the __save_dict_meas__, then calls the autosave."""
        self.make_measurement_save_dict()
        load_save_functions.autosave_preset(self._current_measurement_preset[0], self.__save_dict_meas__, False)

    def new_device_preset(self):
        file = QFileDialog.getSaveFileName(self, 'Save Device Preset', load_save_functions.preset_path, '*.predev')[0]
        if not len(file):
            return
        preset_name = file.split('/')[-1][:-7]
        load_save_functions.save_preset(file, {'_current_device_preset': [preset_name], 'active_devices_dict': {}, 'lineEdit_device_search': ''})
        self.comboBox_device_preset.addItem(preset_name)
        self.comboBox_device_preset.setCurrentText(preset_name)
        self._current_device_preset[0] = preset_name

    def new_measurement_preset(self):
        file = QFileDialog.getSaveFileName(self, 'Save Measurement Preset', load_save_functions.preset_path, '*.premeas')[0]
        if not len(file):
            return
        preset_name = file.split('/')[-1][:-8]
        load_save_functions.save_preset(file, {'_current_measurement_preset': [preset_name], 'protocols_dict': {}})
        self.comboBox_measurement_preset.addItem(preset_name)
        self.comboBox_measurement_preset.setCurrentText(preset_name)
        self._current_measurement_preset[0] = preset_name

    def save_device_preset_as(self):
        """Opens a QFileDialog to save the device preset. A backup / autosave of the preset is made automatically."""
        file = QFileDialog.getSaveFileName(self, 'Save Device Preset', load_save_functions.preset_path, '*.predev')[0]
        if not len(file):
            return
        preset_name = file.split('/')[-1][:-7]
        self.saving = True
        self.comboBox_device_preset.addItem(preset_name)
        self.comboBox_device_preset.setCurrentText(preset_name)
        self._current_device_preset[0] = preset_name
        self.make_device_save_dict()
        load_save_functions.save_preset(file, self.__save_dict_devices__)
        self.saving = False

    def load_backup_device_preset(self):
        file = QFileDialog.getOpenFileName(self, 'Open Device Preset', f'{load_save_functions.preset_path}/Backup', '*.predev')[0]
        if not len(file):
            return
        preset_name = file.split('_')[-1][:-7]
        preset = f'Backup/{file.split("/")[-2]}/{file.split("/")[-1][:-7]}'
        self.save_device_state()
        self._current_device_preset[0] = preset_name
        self.load_device_preset(preset)

    def load_backup_measurement_preset(self):
        file = QFileDialog.getOpenFileName(self, 'Open Measurement Preset', f'{load_save_functions.preset_path}/Backup', '*.premeas')[0]
        if not len(file):
            return
        preset_name = file.split('_')[-1][:-8]
        preset = f'Backup/{file.split("/")[-2]}/{file.split("/")[-1][:-8]}'
        self.save_measurement_state()
        self._current_measurement_preset[0] = preset_name
        self.load_measurement_preset(preset)

    def save_measurement_preset_as(self):
        """Opens a QFileDialog to save the device preset. A backup / autosave of the preset is made automatically."""
        file = QFileDialog.getSaveFileName(self, 'Save Measurement Preset', load_save_functions.preset_path, '*.premeas')[0]
        if not len(file):
            return
        preset_name = file.split('/')[-1][:-8]
        self.saving = True
        self.comboBox_measurement_preset.addItem(preset_name)
        self.comboBox_measurement_preset.setCurrentText(preset_name)
        self._current_measurement_preset[0] = preset_name
        self.make_measurement_save_dict()
        load_save_functions.save_preset(file, self.__save_dict_meas__)
        self.saving = False

    def load_state(self):
        """Loads a specific state of the provided task."""
        predev, premeas = load_save_functions.get_most_recent_presets()
        if predev is not None:
            self.load_device_preset(predev)
        else:
            self.save_device_state()
        if premeas is not None:
            self.load_measurement_preset(premeas)
        else:
            self.save_measurement_state()

    def change_device_preset(self, preset):
        """saves the old device preset, then changes to / loads the new preset."""
        self.save_device_state()
        self._current_device_preset[0] = preset
        self.load_device_preset(preset)

    def change_measurement_preset(self, preset):
        """saves the old measurement preset, then changes to / loads the new preset."""
        self.save_measurement_state()
        self._current_measurement_preset[0] = preset
        self.load_measurement_preset(preset)

    def load_device_preset(self, preset):
        """Called when the comboBox_device_preset is changed (or when loading the last state). Opens the given preset."""
        if self.saving:
            return
        # self.save_device_state()
        with open(f'{load_save_functions.preset_path}{preset}.predev', 'r') as f:
            preset_dict = json.load(f)
        load_save_functions.load_save_dict(preset_dict, self.device_save_dict)
        self.pushButton_make_EPICS_environment.setEnabled(True)
        self.comboBox_device_preset.setCurrentText(self._current_device_preset[0])
        self.build_devices_tree()
        self.update_channels()
        variables_handling.dev_preset = self._current_device_preset[0]
        # for d in self.active_devices_dict:
        #     info = self.active_devices_dict[d]
        #     try:
        #         package_name = info['name'].replace(' ', '_')
        #         info.update({'py_package': importlib.import_module(f'{package_name}.{package_name}')})
        #     except Exception as e:
        #         print(e)

    def update_channels(self):
        variables_handling.channels.clear()
        for key, dev in self.active_devices_dict.items():
            for channel in dev.channels:
                variables_handling.channels.update({channel: dev.channels[channel]})

    def load_measurement_preset(self, premeas):
        """Called when the comboBox_measurement_preset is changed (or when loading the last state). Opens the given preset."""
        if self.saving:
            return
        # self.save_measurement_state()
        with open(f'{load_save_functions.preset_path}{premeas}.premeas', 'r') as f:
            preset_dict = json.load(f)
        load_save_functions.load_save_dict(preset_dict, self.meas_save_dict)
        self.comboBox_measurement_preset.setCurrentText(self._current_measurement_preset[0])
        self.build_protocol_list()
        variables_handling.meas_preset = premeas

    def make_device_save_dict(self):
        """Creates / Updates the __save_dict_devices__"""
        self.get_device_config()
        for key in self.device_save_dict:
            add_string = load_save_functions.get_save_str(self.device_save_dict[key])
            if add_string is not None:
                self.__save_dict_devices__.update({key: load_save_functions.get_save_str(self.device_save_dict[key])})

    def make_measurement_save_dict(self):
        """Creates / Updates the __save_dict_meas__"""
        self.get_step_config()
        self.update_loop_step_order()
        for key in self.meas_save_dict:
            add_string = load_save_functions.get_save_str(self.meas_save_dict[key])
            if add_string is not None:
                self.__save_dict_meas__.update({key: load_save_functions.get_save_str(self.meas_save_dict[key])})

    # --------------------------------------------------
    # Threads - general
    # --------------------------------------------------
    def thread_finished(self):
        """When a QThread calls this, the cursor is set back to the ArrowCursor."""
        self.setCursor(Qt.ArrowCursor)
        self.pushButton_run_protocol.setText('Run selected protocol(s)')
        self.run_thread = None

    def change_progressBar_value(self, val):
        """Sets the progressBar_devices to the given val."""
        self.progressBar_devices.setValue(val)

    def change_progressBar_value_meas(self, val):
        self.progressBar_protocols.setValue(val)

    # --------------------------------------------------
    # devices methods
    # --------------------------------------------------
    def remove_device(self):
        """Opens a dialog to confirm removing the device, then pops it from the active_devices_dict."""
        index = self.treeView_devices.selectedIndexes()[0]
        dat = self.item_model_devices.itemFromIndex(index).data()
        if dat is not None and not dat.startswith('tag:'):
            remove_dialog = QMessageBox.question(self, 'Remove device?', f'Are you sure you want to remove the device {dat}?', QMessageBox.Yes | QMessageBox.No)
            if remove_dialog == QMessageBox.Yes:
                self.active_devices_dict.pop(dat)
                self.build_devices_tree()
                self.update_channels()

    def add_device(self):
        """Opens the dialog to add a device. The returned values of the dialog are inserted to the available devices."""
        add_dialog = AddDeviceDialog(active_devices_dict=self.active_devices_dict, parent=self)
        if add_dialog.exec_():
            self.active_devices_dict = add_dialog.active_devices_dict
        self.build_devices_tree()
        self.update_channels()
        self.pushButton_make_EPICS_environment.setEnabled(True)

    def tree_click(self):
        """Called when clicking the treeView_devices. If the selected index is a device, it will call the config-Widget, and, if possible, save the settings of the last opened config-widget."""
        index = self.treeView_devices.selectedIndexes()[0]
        dat = self.item_model_devices.itemFromIndex(index).data()
        if dat is not None and not dat.startswith('tag:'):
            py_package = importlib.import_module(f'{dat}.{dat}')
            self.get_device_config()
            self.device_config_widget = py_package.subclass_config(self, dat, self.active_devices_dict[dat].settings, self.active_devices_dict[dat].config)
            self.devices_splitter.replaceWidget(2, self.device_config_widget)

    def get_device_config(self):
        """If the currently used device_config_widget has the attribute data, the settings will be updated to the active_devices_dict."""
        if hasattr(self.device_config_widget, 'data'):
            if self.device_config_widget.data in self.active_devices_dict:
                self.active_devices_dict[self.device_config_widget.data].settings = self.device_config_widget.get_settings()
                self.active_devices_dict[self.device_config_widget.data].config = self.device_config_widget.get_config()

    def build_devices_tree(self):
        """Builds the tree of devices.
        First it clears the tree and then iterates through all available devices in device_dict.
        If a search_text is given, only devices whose name includes the string in search_text are added to the tree."""
        for i in range(3):
            item = self.item_model_devices.item(i,0)
            while item.rowCount() > 0:
                item.removeRow(0)
        tags = []
        search_text = self.lineEdit_device_search.text()
        for key, device in sorted(self.active_devices_dict.items()):
            if search_text.lower() not in key.lower():
                continue
            item = QStandardItem(key)
            item.setEditable(False)
            item.setData(key)
            if device.virtual:
                self.item_model_devices.item(1,0).appendRow(item)
            else:
                self.item_model_devices.item(0,0).appendRow(item)
            for tag in device.tags:
                item = QStandardItem(key)
                item.setEditable(False)
                item.setData(key)
                if tag not in tags:
                    tag_item = QStandardItem(tag)
                    tag_item.setEditable(False)
                    tag_item.setData(f'tag:{tag}')
                    self.item_model_devices.item(2,0).appendRow([tag_item])
                    tags.append(tag)
                else:
                    ind = treeView_functions.getItemIndex(self.item_model_devices, f'tag:{tag}')
                    tag_item = self.item_model_devices.itemFromIndex(ind)
                tag_item.appendRow([item])

    # EPICS
    def make_epics_environment(self):
        """Calls the QThread Make_Ioc, creating an IOC with the specified devices."""
        self.setCursor(Qt.WaitCursor)
        self.get_device_config()
        self.make_thread = qthreads.Make_Ioc(self._current_device_preset[0], self.active_devices_dict)
        self.make_thread.sig_step.connect(self.change_progressBar_value)
        self.make_thread.info_step.connect(self.update_console_output)
        self.make_thread.finished.connect(self.thread_finished)
        self.make_thread.start()

    def show_console_output(self):
        """Shows / hides the textEdit_console_output."""
        if self.textEdit_console_output.isHidden():
            self.textEdit_console_output.setHidden(False)
            self.pushButton_show_console_output.setText('Hide console output')
        else:
            self.textEdit_console_output.setHidden(True)
            self.pushButton_show_console_output.setText('Show console output')

    def update_console_output(self, info):
        """Appends the given info to the current console output."""
        self.textEdit_console_output.append(info)

    # --------------------------------------------------
    # measurement methods
    # --------------------------------------------------
    def update_protocol_output(self, info):
        self.textEdit_console_output_meas.append(info)

    def run_current_protocol(self):
        self.update_loop_step_order()
        self.get_device_config()
        if self.run_thread is not None:
            self.run_thread.terminate()
            self.pushButton_run_protocol.setText('Run selected protocol(s)')
            return
        if self.current_protocol is None:
            raise Exception('You need to select a protocol!')
        self.setCursor(Qt.WaitCursor)
        path = f"{self.preferences['py_files_path']}/{self.current_protocol.name}.py"
        self.run_thread = qthreads.Run_Protocol(self.current_protocol, path)
        self.run_thread.sig_step.connect(self.change_progressBar_value_meas)
        self.run_thread.info_step.connect(self.update_protocol_output)
        self.run_thread.finished.connect(self.thread_finished)
        self.pushButton_run_protocol.setText('Abort Run')
        self.run_thread.start()

    def build_current_protocol(self):
        self.update_loop_step_order()
        self.get_device_config()
        if self.current_protocol is None:
            raise Exception('You need to select a protocol!')
        path = f"{self.preferences['py_files_path']}/{self.current_protocol.name}.py"
        bluesky_handling.build_protocol(self.current_protocol, path)

    def tree_click_sequence(self, general=False):
        """Called when clicking the treeView_protocol_sequence."""
        self.update_loop_step_order()
        self.get_step_config()
        self.current_protocol.update_variables()
        config = None
        if general:
            config = General_Protocol_Settings(self, self.current_protocol)
        else:
            index = self.treeView_protocol_sequence.selectedIndexes()[0]
            dat = self.item_model_sequence.itemFromIndex(index).data()
            if dat is not None:
                step = self.current_protocol.loop_step_dict[dat]
                config = make_step_of_type.get_config(step)
                # config = drag_drop_tree_view.config_from_type(step)
        if config is not None:
            if self.loop_step_configuration_widget is not None:
                self.configuration_main_widget.layout().removeWidget(self.loop_step_configuration_widget)
                self.loop_step_configuration_widget.deleteLater()
            self.loop_step_configuration_widget = config
            self.configuration_main_widget.layout().addWidget(self.loop_step_configuration_widget, 1, 0)
            if not general:
                self.loop_step_configuration_widget.name_changed.connect(self.change_step_name)

    def change_step_name(self):
        """Called when a loop_step changes its name, then updates the shown sequence, and also the protocol-data."""
        self.build_protocol_sequence()
        self.update_loop_step_order()

    def get_step_config(self):
        """Updates the data in the currently-to-configure loop_step."""
        if self.loop_step_configuration_widget is not None:
            self.loop_step_configuration_widget.update_step_config()


    def add_protocol(self):
        """Adds a new protocol 'Unnamed_Protocol' to the list. Makes sure that it has a unique filename."""
        name = self.unique_protocol_name('Unnamed_Protocol')
        protocol = {name: Measurement_Protocol(name=name)}
        self.protocols_dict.update(protocol)
        self.build_protocol_list()

    def remove_protocol(self):
        """Opens a dialog to make sure, then removes the selected protocol."""
        index = self.listView_protocols.selectedIndexes()[0]
        dat = self.item_model_protocols.itemFromIndex(index).data()
        if dat is not None:
            remove_dialog = QMessageBox.question(self, 'Delete protocol?', f'Are you sure you want to delete the protocol {dat}?', QMessageBox.Yes | QMessageBox.No)
            if remove_dialog == QMessageBox.Yes:
                self.protocols_dict.pop(dat)
                self.build_protocol_list()

    def change_protocol_name(self, item):
        """Changes the name of the protocol inside the protocols_dict.
        Arguments:
            - item: the item of the protocol, the data is used to get the old name, the new text is checked to be unique."""
        if self.inside_function:
            return
        old_name = item.data()
        protocol_data = self.protocols_dict.pop(old_name)
        new_name = self.unique_protocol_name(item.text())
        self.inside_function = True
        item.setText(new_name)
        item.setData(new_name)
        self.inside_function = False
        self.protocols_dict.update({new_name: protocol_data})
        self.protocols_dict[new_name].name = new_name
        self.build_protocol_list()

    def unique_protocol_name(self, name):
        """Checks if 'name' is already inside the protocols_dict, if yes, _i is added until i is a not yet used number."""
        if name in self.protocols_dict:
            i = 2
            while True:
                if f'{name}_{i}' not in self.protocols_dict:
                    return f'{name}_{i}'
                i += 1
        else:
            return name

    def build_protocol_list(self):
        """Rebuilds the listView_protocols / the item_model_protocols."""
        self.item_model_protocols.clear()
        for protocol in sorted(self.protocols_dict, key=lambda x: x.lower()):
            item = QStandardItem(protocol)
            item.setCheckable(True)
            item.setData(protocol)
            self.item_model_protocols.appendRow(item)

    def show_meas_output(self):
        """Shows / hides the textEdit_console_output."""
        if self.textEdit_console_output_meas.isHidden():
            self.textEdit_console_output_meas.setHidden(False)
            self.pushButton_show_output_meas.setText('Hide console output')
        else:
            self.textEdit_console_output_meas.setHidden(True)
            self.pushButton_show_output_meas.setText('Show console output')

    def protocol_selected(self):
        self.update_loop_step_order()
        self.build_protocol_sequence()
        self.tree_click_sequence(True)

    def build_protocol_sequence(self):
        """Shows / builds the protocol sequence in the treeView dependent on the loop_steps in the current_protocol."""
        ind = self.listView_protocols.selectedIndexes()
        if not ind:
            return
        ind = ind[0]
        ind_seq = self.treeView_protocol_sequence.selectedIndexes()
        sel_data = ''
        if ind_seq:
            sel_data = self.item_model_sequence.data(ind_seq[0])
        prot_name = self.item_model_protocols.itemFromIndex(ind).data()
        protocol = self.protocols_dict[prot_name]
        self.current_protocol = protocol
        variables_handling.protocol_variables = self.current_protocol.variables
        variables_handling.loop_step_variables = self.current_protocol.loop_step_variables
        self.item_model_sequence.clear()
        for loop_step in protocol.loop_steps:
            loop_step.append_to_model(self.item_model_sequence)
        self.treeView_protocol_sequence.expandAll()
        self.sequence_main_widget.setEnabled(True)
        if sel_data is not None:
            new_index = treeView_functions.getItemIndex(self.item_model_sequence, sel_data)
            if new_index:
                self.treeView_protocol_sequence.selectionModel().select(new_index, QItemSelectionModel.Select)

    def sequence_right_click(self, pos):
        """Opens a specific Menu on right click in the protocol-sequence.
        If selection is not on a loop_step, it consists only of Add Step, otherwise it consists of Delete Step."""
        # TODO other actions
        # TODO more beautiful?
        menu = QMenu()
        inds = self.treeView_protocol_sequence.selectedIndexes()
        if inds:
            item = self.item_model_sequence.itemFromIndex(inds[0])
            del_action = QAction('Delete Step')
            del_action.triggered.connect(lambda x: self.remove_loop_step(True))
            below_actions = []
            above_actions = []
            into_actions = []
            row = inds[0].row()
            parent = item.parent()
            if parent is not None:
                parent = parent.data()
            # for stp in sorted(drag_drop_tree_view.step_types, key=lambda x: x.lower()):
            device_steps = make_step_of_type.get_device_steps()
            for stp in sorted(make_step_of_type.step_type_config.keys(), key=lambda x: x.lower()):
                action = QAction(stp)
                action_a = QAction(stp)
                action_in = QAction(stp)
                action.triggered.connect(lambda state, x=stp, y=row+1, z=parent: self.add_loop_step(x, y, z))
                action_a.triggered.connect(lambda state, x=stp, y=row, z=parent: self.add_loop_step(x, y, z))
                action_in.triggered.connect(lambda state, x=stp, y=-1, z=item.data(): self.add_loop_step(x,y,z))
                below_actions.append(action)
                above_actions.append(action_a)
                into_actions.append(action_in)
            device_actions = []
            device_actions_a = []
            device_actions_in = []
            for stp in make_step_of_type.get_device_steps():
                action = QAction(stp)
                action_a = QAction(stp)
                action_in = QAction(stp)
                action.triggered.connect(lambda state, x=stp, y=row+1, z=parent: self.add_loop_step(x, y, z))
                action_a.triggered.connect(lambda state, x=stp, y=row, z=parent: self.add_loop_step(x, y, z))
                action_in.triggered.connect(lambda state, x=stp, y=-1, z=item.data(): self.add_loop_step(x,y,z))
                device_actions.append(action)
                device_actions_a.append(action_a)
                device_actions_in.append(action_in)
            insert_above_menu = QMenu('Insert Above')
            insert_above_menu.addActions(above_actions)
            insert_below_menu = QMenu('Insert Below')
            insert_below_menu.addActions(below_actions)
            if device_actions:
                insert_above_menu.addSeparator()
                insert_above_menu.addActions(device_actions_a)
                insert_below_menu.addSeparator()
                insert_below_menu.addActions(device_actions)
            if self.current_protocol.loop_step_dict[item.data()].has_children:
                add_in_menu = QMenu('Add Into')
                add_in_menu.addActions(into_actions)
                menu.addMenu(add_in_menu)
                if device_actions:
                    add_in_menu.addSeparator()
                    add_in_menu.addActions(device_actions_in)
            menu.addMenu(insert_above_menu)
            menu.addMenu(insert_below_menu)
            menu.addSeparator()
            cut_action = QAction('Cut')
            cut_action.triggered.connect(lambda state, x=item.data(): self.cut_loop_step(x))
            copy_action = QAction('Copy')
            copy_action.triggered.connect(lambda state, x=item.data(): self.copy_loop_step(x))
            paste_menu = QMenu('Paste')
            if self.copied_loop_step is not None:
                paste_above = QAction('Paste Above')
                paste_above.triggered.connect(lambda state, x=True, y=row, z=parent: self.add_loop_step(copied_step=x, position=y, parent=z))
                paste_below = QAction('Paste Below')
                paste_below.triggered.connect(lambda state, x=True, y=row+1, z=parent: self.add_loop_step(copied_step=x, position=y, parent=z))
                if self.current_protocol.loop_step_dict[item.data()].has_children:
                    paste_into = QAction('Paste Into')
                    paste_into.triggered.connect(lambda state, x=True, y=-1, z=item.data(): self.add_loop_step(copied_step=x,position=y,parent=z))
                    paste_menu.addAction(paste_into)
                paste_menu.addActions([paste_above, paste_below])
            else:
                paste_menu.setEnabled(False)
            menu.addAction(cut_action)
            menu.addAction(copy_action)
            menu.addMenu(paste_menu)
            menu.addSeparator()
            menu.addAction(del_action)
        else:
            add_actions = []
            # for stp in sorted(drag_drop_tree_view.step_types, key=lambda x: x.lower()):
            for stp in sorted(make_step_of_type.step_type_config, key=lambda x: x.lower()):
                action = QAction(stp)
                action.triggered.connect(lambda state, x=stp: self.add_loop_step(x))
                add_actions.append(action)
            device_actions = []
            for stp in make_step_of_type.get_device_steps():
                action = QAction(stp)
                action.triggered.connect(lambda state, x=stp: self.add_loop_step(x))
                device_actions.append(action)
            add_menu = QMenu('Add Step')
            add_menu.addActions(add_actions)
            if device_actions:
                add_menu.addSeparator()
                add_menu.addActions(device_actions)
            paste_action = QAction('Paste')
            if self.copied_loop_step is not None:
                paste_action.triggered.connect(lambda state, x=True, y=-1, z=None: self.add_loop_step(copied_step=x, position=y, parent=z))
            else:
                paste_action.setEnabled(False)
            menu.addMenu(add_menu)
            menu.addAction(paste_action)
        menu.exec_(self.treeView_protocol_sequence.viewport().mapToGlobal(pos))

    def cut_loop_step(self, step_name):
        """Copies the given step, then removes it."""
        self.copy_loop_step(step_name)
        self.remove_loop_step(ask=False)

    def copy_loop_step(self, step_name):
        """Makes a deepcopy of the given step and stores it in copied_loop_step."""
        self.copied_loop_step = deepcopy(self.current_protocol.loop_step_dict[step_name])


    def move_loop_step(self, up_down=0, in_out=0):
        """Moves a loop_step up or down in the sequence. It can also moved in or out (into the loop_step above, it if accepts children).
        Arguments:
            - up_down: Default 0, moves up if negative (lower row-number), down if positive
            - in_out: moves in if positive, out if negative, default 0"""
        move_command = change_sequence.CommandMoveStep(self.treeView_protocol_sequence, self.item_model_sequence, up_down, in_out, self.current_protocol.loop_step_dict, self.update_loop_step_order)
        self.undo_stack.push(move_command)
        self.actionUndo.setEnabled(self.undo_stack.canUndo())
        self.actionRedo.setEnabled(self.undo_stack.canRedo())
        # TODO make function more clear and simple
        # ind = self.treeView_protocol_sequence.selectedIndexes()[0]
        # item = self.item_model_sequence.itemFromIndex(ind)
        # parent = item.parent()
        # if parent is None:
        #     if up_down != 0 and (ind.row() > 0 or up_down > 0) and (ind.row() < self.item_model_sequence.rowCount()-1 or up_down < 0):
        #         row = self.item_model_sequence.takeRow(ind.row())
        #         self.item_model_sequence.insertRow(ind.row() + up_down, row)
        #     elif in_out > 0 and ind.row() > 0:
        #         above = self.item_model_sequence.item(ind.row()-1, 0)
        #         if self.current_protocol.loop_step_dict[above.data()].has_children:
        #             row = self.item_model_sequence.takeRow(ind.row())
        #             above.insertRow(above.rowCount(), row)
        # else:
        #     if up_down != 0 and (ind.row() > 0 or up_down > 0) and (ind.row() < parent.rowCount()-1 or up_down < 0):
        #         row = parent.takeRow(ind.row())
        #         parent.insertRow(ind.row() + up_down, row)
        #     elif in_out > 0 and ind.row() > 0:
        #         above = parent.child(ind.row()-1, 0)
        #         if self.current_protocol.loop_step_dict[above.data()].has_children:
        #             row = parent.takeRow(ind.row())
        #             above.insertRow(above.rowCount(), row)
        #     elif in_out < 0:
        #         grandparent = parent.parent()
        #         if grandparent is None:
        #             grandparent = self.item_model_sequence
        #         parent_row = parent.index().row()
        #         row = parent.takeRow(ind.row())
        #         grandparent.insertRow(parent_row+1, row)
        # self.treeView_protocol_sequence.clearSelection()
        # new_ind = self.item_model_sequence.indexFromItem(item)
        # self.treeView_protocol_sequence.selectionModel().select(new_ind, QItemSelectionModel.Select)

    def add_loop_step(self, step_type='', position=-1, parent=None, copied_step=False):
        """Add a loop_step of given step_type. Updates the current sequence into the protocol, then initializes the new step.
        Arguments:
            - step_type: string giving the type of step to be added
            - position: where to add the step, default -1, append to the end
            - parent: if None, the step is added to the outermost layer of the protocol, otherwise inside the parent
            - copied_step: if None, a new step of type step_type will be created, otherwise copied_loop_step will be inserted"""
        self.update_loop_step_order()
        if copied_step:
            step = self.copied_loop_step
        else:
            # step = drag_drop_tree_view.get_loop_step_from_type(step_type)
            step = make_step_of_type.make_step(step_type)
        self.current_protocol.add_loop_step_rec(step, model=self.item_model_sequence, position=position, parent_step_name=parent)
        self.build_protocol_sequence()
        if copied_step:
            self.copy_loop_step(self.copied_loop_step.full_name)
        new_ind = treeView_functions.getItemIndex(self.item_model_sequence, step.full_name)
        self.treeView_protocol_sequence.selectionModel().select(new_ind, QItemSelectionModel.Select)

    def remove_loop_step(self, ask=True):
        """After updating the loop_step order in the protocol, the selected loop step is deleted (if the messagebox is accepted)."""
        self.update_loop_step_order()
        ind = self.treeView_protocol_sequence.selectedIndexes()[0]
        name = self.item_model_sequence.itemFromIndex(ind).data()
        if name is not None:
            remove_dialog = None
            if ask:
                remove_dialog = QMessageBox.question(self, 'Delete Step?', f'Are you sure you want to delete the step {name}?', QMessageBox.Yes | QMessageBox.No)
            if not ask or remove_dialog == QMessageBox.Yes:
                self.current_protocol.remove_loop_step(name)
                self.build_protocol_sequence()

    def update_loop_step_order(self):
        """Goes through all the loop_steps in the sequence, then rearranges them in the protocol."""
        if self.current_protocol is not None:
            loop_steps = []
            for i in range(self.item_model_sequence.rowCount()):
                item = self.item_model_sequence.item(i, 0)
                sub_steps = treeView_functions.get_substeps(item)
                loop_steps.append((item.data(), sub_steps))
            self.current_protocol.rearrange_loop_steps(loop_steps)




if __name__ == '__main__':
    sys.excepthook = exception_hook.exception_hook
    app = QCoreApplication.instance()
    if app is None:
        app = QApplication(sys.argv)
    ui = MainWindow()
    ui.show()
    ui.showMaximized()
    app.exec_()
