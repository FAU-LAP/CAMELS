from PyQt5.QtGui import QStandardItemModel, QStandardItem
from PyQt5.QtCore import Qt, QSize, pyqtSignal
from PyQt5.QtWidgets import QWidget, QGridLayout, QLabel, QLineEdit, QAction


from utility import treeView_functions



class Loop_Step:
    """Main Class for all Loop_Steps.
    Attributes:
        - step_type: should be overwritten on inheritance, gives the type of Loop_Step
        - has_children: set to True if a loop_step accepts children
        - name: specification of the loop_step (other than the type)
        - full name: consists of the type and name
        - parent_step: the loop_steps name which contains this step"""
    def __init__(self, name='', parent_step=None):
        self.step_type = 'Default'
        self.__save_dict__ = {}
        self.has_children = False
        self.name = name
        self.full_name = f'{self.step_type} ({name})'
        self.parent_step = parent_step

    def update_full_name(self):
        """Updates the full_name by combination of step_type and name"""
        self.full_name = f'{self.step_type} ({self.name})'

    def append_to_model(self, item_model, parent=None):
        """Ensures that the (full_)name of the loop_step is unique and updates name and full_name, then appends the step to the model."""
        if parent is None:
            parent = item_model
        if type(parent) is str:
            parent = item_model.itemFromIndex(treeView_functions.getItemIndex(item_model, parent))
        self.full_name = f'{self.step_type} ({self.name})'
        name = self.full_name
        if treeView_functions.getItemIndex(item_model, name) is not None:
            i = 1
            name = f'{name[:-1]}_{i})'
            while treeView_functions.getItemIndex(item_model, name) is not None:
                name = f'{name[:-3]}_{i})'
                i += 1
            self.name = name[len(self.step_type)+2:-1]
        item = QStandardItem(name)
        item.setData(name)
        parent.appendRow(item)
        index = treeView_functions.getItemIndex(item_model, name)
        item_model.setData(index, QSize(20,20), Qt.SizeHintRole)
        item.setDropEnabled(False)
        self.full_name = name
        return item

    def get_protocol_string(self):
        return f'# {self.full_name}\n'


class Loop_Step_Container(Loop_Step):
    """Parent Class for loop_steps that should contain further steps (like e.g. a for-loop)."""
    def __init__(self, name='', children=None, parent_step=None):
        super().__init__(name, parent_step=parent_step)
        self.step_type = 'Container'
        self.has_children = True
        if children is None:
            children = []
        self.children = children

    def append_to_model(self, item_model:QStandardItemModel, parent=None):
        """Overwrites this function to additionally append all children to the model."""
        item = super().append_to_model(item_model, parent)
        item.setDropEnabled(True)
        item.setEditable(False)
        for child in self.children:
            child.append_to_model(item_model, item)

    def add_child(self, child, position=-1):
        """Add a child-step at the specified position, default is -1, meaning to append at the end."""
        if position < 0:
            self.children.append(child)
        else:
            self.children.insert(position, child)

    def remove_child(self, child):
        """Removes the specified child from the children."""
        self.children.remove(child)

    def get_protocol_string(self):
        protocol_string = super().get_protocol_string()
        protocol_string += self.get_children_strings()
        return protocol_string

    def get_children_strings(self):
        child_string = ''
        for child in self.children:
            child_string += child.get_protocol_string()
        return child_string


class Loop_Step_Config(QWidget):
    """Parent class for the configuration Widget of the loop_step. Provides the main layout and a lineEdit for changing the loop_steps name."""
    name_changed = pyqtSignal()

    def __init__(self, parent=None, loop_step=None):
        super(Loop_Step_Config, self).__init__(parent)
        layout = QGridLayout()
        self.name_widget = Loop_Step_Name_Widget(self, loop_step.name)
        self.loop_step = loop_step
        self.name_widget.name_changed.connect(self.change_name)
        layout.addWidget(self.name_widget, 0, 0)
        self.setLayout(layout)

    def change_name(self, name):
        """Changes the name of the loop_step, then emits the name_changed signal."""
        self.loop_step.name = name
        self.loop_step.update_full_name()
        self.name_changed.emit()

    def update_step_config(self):
        """Overwrite this for specific step-configuration. It should provide the loop_step object with all necessary data."""
        self.name_widget.change_name()

class Loop_Step_Name_Widget(QWidget):
    name_changed = pyqtSignal(str)

    def __init__(self, parent=None, name=''):
        super().__init__(parent)
        label = QLabel('Name:')
        self.lineEdit_name = QLineEdit(name, self)
        layout = QGridLayout()
        layout.addWidget(label, 0, 0)
        layout.addWidget(self.lineEdit_name, 0, 1)
        self.setLayout(layout)
        layout.setContentsMargins(0, 0, 0, 0)

        self.lineEdit_name.returnPressed.connect(self.change_name)

    def change_name(self):
        self.name_changed.emit(self.lineEdit_name.text())
