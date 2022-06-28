# -*- coding: utf-8 -*-

# Form implementation generated from reading ui file 'installer_window.ui'
#
# Created by: PyQt5 UI code generator 5.15.6
#
# WARNING: Any manual changes made to this file will be lost when pyuic5 is
# run again.  Do not edit this file unless you know what you are doing.


from PyQt5 import QtCore, QtGui, QtWidgets


class Ui_InstallerWindow(object):
    def setupUi(self, InstallerWindow):
        InstallerWindow.setObjectName("InstallerWindow")
        InstallerWindow.resize(800, 600)
        self.centralwidget = QtWidgets.QWidget(InstallerWindow)
        self.centralwidget.setObjectName("centralwidget")
        self.gridLayout = QtWidgets.QGridLayout(self.centralwidget)
        self.gridLayout.setObjectName("gridLayout")
        self.labela = QtWidgets.QLabel(self.centralwidget)
        font = QtGui.QFont()
        font.setFamily("Calibri")
        font.setPointSize(14)
        font.setBold(True)
        font.setWeight(75)
        self.labela.setFont(font)
        self.labela.setObjectName("labela")
        self.gridLayout.addWidget(self.labela, 1, 1, 1, 1)
        self.label_2t = QtWidgets.QLabel(self.centralwidget)
        self.label_2t.setObjectName("label_2t")
        self.gridLayout.addWidget(self.label_2t, 2, 1, 1, 1)
        spacerItem = QtWidgets.QSpacerItem(20, 40, QtWidgets.QSizePolicy.Minimum, QtWidgets.QSizePolicy.Expanding)
        self.gridLayout.addItem(spacerItem, 3, 1, 1, 1)
        self.groupBox_progress = QtWidgets.QGroupBox(self.centralwidget)
        self.groupBox_progress.setTitle("")
        self.groupBox_progress.setObjectName("groupBox_progress")
        self.gridLayout_4 = QtWidgets.QGridLayout(self.groupBox_progress)
        self.gridLayout_4.setObjectName("gridLayout_4")
        self.label_current_job = QtWidgets.QLabel(self.groupBox_progress)
        self.label_current_job.setObjectName("label_current_job")
        self.gridLayout_4.addWidget(self.label_current_job, 0, 0, 1, 1)
        self.progressBar_installation = QtWidgets.QProgressBar(self.groupBox_progress)
        self.progressBar_installation.setProperty("value", 0)
        self.progressBar_installation.setObjectName("progressBar_installation")
        self.gridLayout_4.addWidget(self.progressBar_installation, 1, 0, 1, 1)
        self.gridLayout.addWidget(self.groupBox_progress, 5, 0, 1, 2)
        self.groupBox_questions = QtWidgets.QGroupBox(self.centralwidget)
        self.groupBox_questions.setTitle("")
        self.groupBox_questions.setObjectName("groupBox_questions")
        self.gridLayout_2 = QtWidgets.QGridLayout(self.groupBox_questions)
        self.gridLayout_2.setObjectName("gridLayout_2")
        self.pushButton_cancel = QtWidgets.QPushButton(self.groupBox_questions)
        self.pushButton_cancel.setObjectName("pushButton_cancel")
        self.gridLayout_2.addWidget(self.pushButton_cancel, 4, 2, 1, 1)
        self.pushButton_install = QtWidgets.QPushButton(self.groupBox_questions)
        self.pushButton_install.setObjectName("pushButton_install")
        self.gridLayout_2.addWidget(self.pushButton_install, 4, 1, 1, 1)
        spacerItem1 = QtWidgets.QSpacerItem(40, 20, QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Minimum)
        self.gridLayout_2.addItem(spacerItem1, 4, 0, 1, 1)
        self.groupBox_custom_install = QtWidgets.QGroupBox(self.groupBox_questions)
        self.groupBox_custom_install.setTitle("")
        self.groupBox_custom_install.setObjectName("groupBox_custom_install")
        self.gridLayout_3 = QtWidgets.QGridLayout(self.groupBox_custom_install)
        self.gridLayout_3.setObjectName("gridLayout_3")
        self.label_3 = QtWidgets.QLabel(self.groupBox_custom_install)
        self.label_3.setObjectName("label_3")
        self.gridLayout_3.addWidget(self.label_3, 5, 0, 1, 1)
        self.pathButton_CAMELS = Path_Button_Edit(self.groupBox_custom_install)
        self.pathButton_CAMELS.setObjectName("pathButton_CAMELS")
        self.gridLayout_3.addWidget(self.pathButton_CAMELS, 5, 1, 1, 1)
        self.checkBox = QtWidgets.QCheckBox(self.groupBox_custom_install)
        self.checkBox.setChecked(True)
        self.checkBox.setObjectName("checkBox")
        self.gridLayout_3.addWidget(self.checkBox, 4, 0, 1, 2)
        self.checkBox_camels = QtWidgets.QCheckBox(self.groupBox_custom_install)
        self.checkBox_camels.setChecked(True)
        self.checkBox_camels.setObjectName("checkBox_camels")
        self.gridLayout_3.addWidget(self.checkBox_camels, 3, 0, 1, 2)
        self.checkBox_epics = QtWidgets.QCheckBox(self.groupBox_custom_install)
        self.checkBox_epics.setChecked(True)
        self.checkBox_epics.setObjectName("checkBox_epics")
        self.gridLayout_3.addWidget(self.checkBox_epics, 1, 0, 1, 2)
        self.checkBox_wsl = QtWidgets.QCheckBox(self.groupBox_custom_install)
        self.checkBox_wsl.setChecked(True)
        self.checkBox_wsl.setObjectName("checkBox_wsl")
        self.gridLayout_3.addWidget(self.checkBox_wsl, 0, 0, 1, 2)
        self.gridLayout_2.addWidget(self.groupBox_custom_install, 3, 0, 1, 3)
        self.radioButton_full = QtWidgets.QRadioButton(self.groupBox_questions)
        self.radioButton_full.setChecked(True)
        self.radioButton_full.setObjectName("radioButton_full")
        self.gridLayout_2.addWidget(self.radioButton_full, 0, 0, 1, 3)
        self.radioButton_custom = QtWidgets.QRadioButton(self.groupBox_questions)
        self.radioButton_custom.setObjectName("radioButton_custom")
        self.gridLayout_2.addWidget(self.radioButton_custom, 1, 0, 1, 3)
        self.gridLayout.addWidget(self.groupBox_questions, 4, 0, 1, 2)
        spacerItem2 = QtWidgets.QSpacerItem(20, 40, QtWidgets.QSizePolicy.Minimum, QtWidgets.QSizePolicy.Expanding)
        self.gridLayout.addItem(spacerItem2, 0, 1, 1, 1)
        self.image_placeholder = QtWidgets.QWidget(self.centralwidget)
        self.image_placeholder.setObjectName("image_placeholder")
        self.gridLayout.addWidget(self.image_placeholder, 0, 0, 4, 1)
        InstallerWindow.setCentralWidget(self.centralwidget)
        self.menubar = QtWidgets.QMenuBar(InstallerWindow)
        self.menubar.setGeometry(QtCore.QRect(0, 0, 800, 21))
        self.menubar.setObjectName("menubar")
        InstallerWindow.setMenuBar(self.menubar)
        self.statusbar = QtWidgets.QStatusBar(InstallerWindow)
        self.statusbar.setObjectName("statusbar")
        InstallerWindow.setStatusBar(self.statusbar)

        self.retranslateUi(InstallerWindow)
        QtCore.QMetaObject.connectSlotsByName(InstallerWindow)

    def retranslateUi(self, InstallerWindow):
        _translate = QtCore.QCoreApplication.translate
        InstallerWindow.setWindowTitle(_translate("InstallerWindow", "MainWindow"))
        self.labela.setText(_translate("InstallerWindow", "CAMELS Installer"))
        self.label_2t.setText(_translate("InstallerWindow", "Configurable Application for Measurements, Experiments and Laboratory-Systems"))
        self.label_current_job.setText(_translate("InstallerWindow", "TextLabel"))
        self.pushButton_cancel.setText(_translate("InstallerWindow", "Cancel"))
        self.pushButton_install.setText(_translate("InstallerWindow", "Install"))
        self.label_3.setText(_translate("InstallerWindow", "Path to CAMELS:"))
        self.checkBox.setText(_translate("InstallerWindow", "Install Python Environment for CAMELS"))
        self.checkBox_camels.setText(_translate("InstallerWindow", "Install CAMELS"))
        self.checkBox_epics.setText(_translate("InstallerWindow", "Install EPICS in WSL"))
        self.checkBox_wsl.setText(_translate("InstallerWindow", "Install WSL"))
        self.radioButton_full.setText(_translate("InstallerWindow", "Full Install (recommended)"))
        self.radioButton_custom.setText(_translate("InstallerWindow", "Custom Install"))
from utility.path_button_edit import Path_Button_Edit
