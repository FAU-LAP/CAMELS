# -*- coding: utf-8 -*-

# Form implementation generated from reading ui file 'fit_definer.ui'
#
# Created by: PyQt5 UI code generator 5.15.6
#
# WARNING: Any manual changes made to this file will be lost when pyuic5 is
# run again.  Do not edit this file unless you know what you are doing.


from PyQt5 import QtCore, QtGui, QtWidgets


class Ui_Fit_Definer(object):
    def setupUi(self, Fit_Definer):
        Fit_Definer.setObjectName("Fit_Definer")
        Fit_Definer.resize(287, 243)
        self.gridLayout = QtWidgets.QGridLayout(Fit_Definer)
        self.gridLayout.setContentsMargins(0, 0, 0, 0)
        self.gridLayout.setObjectName("gridLayout")
        self.radioButton_custom_func = QtWidgets.QRadioButton(Fit_Definer)
        self.radioButton_custom_func.setObjectName("radioButton_custom_func")
        self.gridLayout.addWidget(self.radioButton_custom_func, 1, 1, 1, 1)
        self.checkBox_guess = QtWidgets.QCheckBox(Fit_Definer)
        self.checkBox_guess.setObjectName("checkBox_guess")
        self.gridLayout.addWidget(self.checkBox_guess, 4, 0, 1, 2)
        self.radioButton_predef_func = QtWidgets.QRadioButton(Fit_Definer)
        self.radioButton_predef_func.setChecked(True)
        self.radioButton_predef_func.setObjectName("radioButton_predef_func")
        self.gridLayout.addWidget(self.radioButton_predef_func, 1, 0, 1, 1)
        self.lineEdit_custom_func = QtWidgets.QLineEdit(Fit_Definer)
        self.lineEdit_custom_func.setObjectName("lineEdit_custom_func")
        self.gridLayout.addWidget(self.lineEdit_custom_func, 2, 1, 1, 1)
        self.comboBox_predef_func = QtWidgets.QComboBox(Fit_Definer)
        self.comboBox_predef_func.setObjectName("comboBox_predef_func")
        self.gridLayout.addWidget(self.comboBox_predef_func, 2, 0, 1, 1)
        spacerItem = QtWidgets.QSpacerItem(20, 40, QtWidgets.QSizePolicy.Minimum, QtWidgets.QSizePolicy.Expanding)
        self.gridLayout.addItem(spacerItem, 3, 0, 1, 1)
        self.label = QtWidgets.QLabel(Fit_Definer)
        font = QtGui.QFont()
        font.setPointSize(9)
        font.setBold(True)
        font.setWeight(75)
        self.label.setFont(font)
        self.label.setObjectName("label")
        self.gridLayout.addWidget(self.label, 0, 0, 1, 1)
        self.checkBox_fit = QtWidgets.QCheckBox(Fit_Definer)
        self.checkBox_fit.setObjectName("checkBox_fit")
        self.gridLayout.addWidget(self.checkBox_fit, 0, 1, 1, 1)

        self.retranslateUi(Fit_Definer)
        QtCore.QMetaObject.connectSlotsByName(Fit_Definer)

    def retranslateUi(self, Fit_Definer):
        _translate = QtCore.QCoreApplication.translate
        Fit_Definer.setWindowTitle(_translate("Fit_Definer", "Form"))
        self.radioButton_custom_func.setText(_translate("Fit_Definer", "Custom function"))
        self.checkBox_guess.setText(_translate("Fit_Definer", "guess initial parameters"))
        self.radioButton_predef_func.setText(_translate("Fit_Definer", "Predefined function"))
        self.label.setText(_translate("Fit_Definer", "Fit to: all y-axes"))
        self.checkBox_fit.setText(_translate("Fit_Definer", "fit?"))
