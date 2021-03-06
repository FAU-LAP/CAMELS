import os
import sys
from collections import ChainMap
import threading
import numpy as np
import lmfit

import matplotlib.pyplot as plt
from bluesky.callbacks.mpl_plotting import LivePlot, LiveFitPlot
from bluesky.callbacks import LiveFit
from bluesky.callbacks.core import get_obj_fields
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg,\
    NavigationToolbar2QT

from PyQt5.QtWidgets import QWidget, QGridLayout, QApplication, QPushButton,\
    QTableWidgetItem, QColorDialog, QComboBox
from PyQt5.QtCore import pyqtSignal, QObject, Qt
from PyQt5.QtGui import QIcon

from gui.plot_options import Ui_Plot_Options
from bluesky_handling.evaluation_helper import Evaluator
from ophyd import SignalRO, Device, Component, BlueskyInterface, Kind

dark_mode = False
def activate_dark_mode():
    """Changes the plot-style to dark-mode."""
    global dark_mode
    dark_mode = True
    plt.style.use('dark_background')


class MPLwidget(FigureCanvasQTAgg):
    def __init__(self):
        fig, ax = plt.subplots()
        self.axes = ax
        self.axes.grid()
        super().__init__(fig)

class PlotWidget(QWidget):
    def __init__(self, x_name=None, y_names=(), *, legend_keys=None, xlim=None,
                 ylim=None, epoch='run', parent=None, namespace=None, ylabel='',
                 xlabel='', title='', stream_name='primary', fits=None,
                 do_plot=True, **kwargs):
        super().__init__(parent=parent)
        canvas = MPLwidget()
        if isinstance(y_names, str):
            y_names = [y_names]
        self.ax = canvas.axes
        self.stream_name = stream_name
        self.fits = fits or []
        self.liveFits = []
        self.liveFitPlots = []
        eva = Evaluator(namespace=namespace)
        for fit in fits:
            if fit["use_custom_func"]:
                model = lmfit.models.ExpressionModel(fit["custom_func"])
                label = 'custom'
            else:
                model = lmfit.models.lmfit_models[fit["predef_func"]]()
                label = fit["predef_func"]
            if fit["guess_params"]:
                init_guess = None
            else:
                init_guess = {}
                for i, param in enumerate(fit["initial_params"]['name']):
                    init_guess[param] = fit["initial_params"]['initial value'][i]
            upper = {}
            lower = {}
            for i, param in enumerate(fit['initial_params']['name']):
                upper[param] = fit['initial_params']['upper bound'][i] or np.inf
                lower[param] = fit['initial_params']['lower bound'][i] or -np.inf
            params = model.make_params()
            if init_guess:
                for i, param in enumerate(fit['initial_params']['name']):
                    params[param].set(init_guess[param], min=lower[param],
                                      max=upper[param])
            else:
                for i, param in enumerate(fit['initial_params']['name']):
                    params[param].set(min=lower[param], max=upper[param])

            name = f'{label}_{fit["y"]}_v_{fit["x"]}'
            livefit = LiveFit_Eva(model, fit["y"], {'x': fit["x"]}, init_guess,
                                  evaluator=eva, name=name.replace(' ', '_'),
                                  params=params, stream_name=stream_name)
            self.liveFits.append(livefit)
            self.liveFitPlots.append(Fit_Plot_No_Init_Guess(livefit, ax=self.ax,
                                                            legend_keys=[name]))
        self.livePlot = MultiLivePlot(y_names, x_name, legend_keys=legend_keys,
                                      xlim=xlim, ylim=ylim, epoch=epoch,
                                      ax=canvas.axes, evaluator=eva,
                                      xlabel=xlabel, ylabel=ylabel, title=title,
                                      stream_name=stream_name, do_plot=do_plot,
                                      fitPlots=self.liveFitPlots, **kwargs)
        self.livePlot.new_data.connect(self.show)
        self.toolbar = NavigationToolbar2QT(canvas, self)


        self.pushButton_show_options = QPushButton('Show Options')
        self.pushButton_show_options.clicked.connect(self.show_options)
        self.pushButton_autoscale = QPushButton('Autoscale')
        self.pushButton_autoscale.clicked.connect(self.autoscale)
        self.plot_options = Plot_Options(self, self.ax, self.livePlot)

        layout = QGridLayout()
        layout.addWidget(canvas, 0, 1, 1, 3)
        layout.addWidget(self.toolbar, 1, 3)
        layout.addWidget(self.pushButton_show_options, 1, 1)
        layout.addWidget(self.pushButton_autoscale, 1, 2)
        layout.addWidget(self.plot_options, 0, 0, 2, 1)
        self.setLayout(layout)

        self.setWindowTitle(title or f'{x_name} vs. {y_names[0]}')
        self.setWindowIcon(QIcon('graphics/CAMELS.svg'))
        print(os.getcwd())

        self.plot_options.hide()
        self.options_open = False
        if do_plot:
            self.show()

    def clear_plot(self):
        self.livePlot.clear_plot()

    def autoscale(self):
        self.ax.autoscale()
        self.ax.figure.canvas.draw_idle()

    def show_options(self):
        if self.options_open:
            self.pushButton_show_options.setText('Show Options')
            self.options_open = False
            self.plot_options.hide()
        else:
            self.pushButton_show_options.setText('Hide Options')
            self.options_open = True
            self.plot_options.show()
        self.adjustSize()


class LiveFit_Eva(LiveFit):
    def __init__(self, model, y, independent_vars, init_guess=None, *,
                 update_every=1, evaluator=None, name='', params=None,
                 stream_name='primary'):
        super().__init__(model=model, y=y, independent_vars=independent_vars,
                         init_guess=init_guess, update_every=update_every)
        # change_name = name.replace(' ', '_').replace(':', '_').replace('.', '_')
        self.eva = evaluator
        self.name = f'{name}_{stream_name}'
        self.params = params
        name = name.replace('(', '').replace(')', '').replace('.', '')
        self.ophyd_fit = Fit_Ophyd(name, name=name, params=params)
        self.stream_name = stream_name


    def event(self, doc):
        idv = {}
        for k, v in self.independent_vars.items():
            try:
                new_x = doc['data'][v]
            except KeyError:
                if v in ('time', 'seq_num'):
                    new_x = doc[v]
                else:
                    if not self.eva.is_to_date(doc['time']):
                        self.eva.event(doc)
                    new_x = self.eva.eval(v)
            idv[k] = new_x

        try:
            y = doc['data'][self.y]
        except KeyError:
            if not self.eva.is_to_date(doc['time']):
                self.eva.event(doc)
            y = self.eva.eval(self.y)
        # Always stash the data for the next time the fit is updated.
        self.update_caches(y, idv)
        self.__stale = True

        # Maybe update the fit or maybe wait.
        if self.update_every is not None:
            i = len(self.ydata)
            N = len(self.model.param_names)
            if i < N:
                # not enough points to fit yet
                pass
            elif (i == N) or ((i - 1) % self.update_every == 0):
                self.update_fit()
                self.ophyd_fit.update_data(self.result, doc['time'])
                # self.ophyd_fit.result = self.result.best_values
                # self.ophyd_fit.timestamp = doc['time']
        super().event(doc)

    def update_fit(self):
        N = len(self.model.param_names)
        if len(self.ydata) < N:
            return
        else:
            kwargs = {}
            kwargs.update(self.independent_vars_data)
            kwargs.update(self.init_guess)
            if self.params:
                self.result = self.model.fit(self.ydata, params=self.params,
                                             **kwargs)
            else:
                self.result = self.model.fit(self.ydata, **kwargs)
            self.__stale = False

class Fit_Signal(SignalRO):
    # def __init__(self,  name, value=0., timestamp=None, parent=None, labels=None, kind='hinted', tolerance=None, rtolerance=None, metadata=None, cl=None, attr_name=''):
    #     super().__init__(name=name, value=value, timestamp=timestamp, parent=parent, labels=labels, kind=kind, tolerance=tolerance, rtolerance=rtolerance, metadata=metadata, cl=cl, attr_name=attr_name)

    def update_data(self, result, timestamp):
        self._readback = result
        self._metadata['timestamp'] = timestamp

class Fit_Ophyd(Device):
    a = Component(Fit_Signal, name='a')
    b = Component(Fit_Signal, name='b')
    c = Component(Fit_Signal, name='c')
    d = Component(Fit_Signal, name='d')
    e = Component(Fit_Signal, name='e')
    f = Component(Fit_Signal, name='f')
    g = Component(Fit_Signal, name='g')
    h = Component(Fit_Signal, name='h')
    i = Component(Fit_Signal, name='i')
    j = Component(Fit_Signal, name='j')
    k = Component(Fit_Signal, name='k')
    l = Component(Fit_Signal, name='l')
    m = Component(Fit_Signal, name='m')
    n = Component(Fit_Signal, name='n')
    o = Component(Fit_Signal, name='o')
    p = Component(Fit_Signal, name='p')
    q = Component(Fit_Signal, name='q')
    r = Component(Fit_Signal, name='r')
    covar = Component(Fit_Signal, name='covar')

    def __init__(self, prefix='', *, name, kind=None, read_attrs=None,
                 configuration_attrs=None, parent=None, params=None, **kwargs):
        super().__init__(prefix=prefix, name=name, kind=kind,
                         read_attrs=read_attrs,
                         configuration_attrs=configuration_attrs, parent=parent,
                         **kwargs)
        self.params = params.keys()
        order = [self.a, self.b, self.c, self.d, self.e, self.f, self.g, self.h,
                 self.i, self.j, self.k, self.l, self.m, self.n, self.o, self.p,
                 self.q, self.r]
        self.used_comps = [self.covar]
        for i, comp in enumerate(self.params):
            order[i].name = f'{name}_{comp}'
            self.used_comps.append(order[i])

    def update_data(self, result, timestamp):
        order = [self.a, self.b, self.c, self.d, self.e, self.f, self.g, self.h,
                 self.i, self.j, self.k, self.l, self.m, self.n, self.o, self.p,
                 self.q, self.r]
        for i, comp in enumerate(self.params):
            order[i].update_data(result.best_values[comp], timestamp)
        self.covar.update_data(result.covar, timestamp)



    def read(self):
        res = BlueskyInterface.read(self)
        i = 1
        for _, component in self._get_components_of_kind(Kind.normal):
            res.update(component.read())
            i += 1
            if i > len(self.params):
                break
        return res



class Fit_Plot_No_Init_Guess(LiveFitPlot):
    def __init__(self, livefit, *, num_points=100, legend_keys=None, xlim=None,
                 ylim=None, ax=None, **kwargs):
        super().__init__(livefit, num_points=num_points, legend_keys=legend_keys,
                         xlim=xlim, ylim=ylim, ax=ax, **kwargs)
        if len(livefit.independent_vars) != 1:
            raise NotImplementedError("LiveFitPlot supports models with one "
                                      "independent variable only.")
        self.__x_key, = livefit.independent_vars.keys()  # this never changes
        x, = livefit.independent_vars.values()  # this may change
        self.num_points = num_points
        self._livefit = livefit
        self._xlim = xlim
        self._has_been_run = False

    def start(self, doc):
        LivePlot.start(self, doc)
        self.livefit.start(doc)
        self.x, = self.livefit.independent_vars.keys()  # in case it changed
        # Put fit above other lines (default 2) but below text (default 3).
        [line.set_zorder(2.5) for line in self.lines]
        if self.legend_keys:
            self.current_line.set_label(self.legend_keys[-1])
        self.ax.legend(loc=0, title='')


    def event(self, doc):
        self.livefit.event(doc)
        if self.livefit.result is not None:
            # Evaluate the model function at equally-spaced points.
            # To determine the domain of x, use xlim if availabe. Otherwise,
            # use the range of x points measured up to this point.
            if self._xlim is None:
                x_data = self.livefit.independent_vars_data[self.__x_key]
                xmin, xmax = np.min(x_data), np.max(x_data)
            else:
                xmin, xmax = self._xlim
            x_points = np.linspace(xmin, xmax, self.num_points)
            kwargs = {self.__x_key: x_points}
            kwargs.update(self.livefit.result.values)
            self.y_data = self.livefit.result.model.eval(**kwargs)
            self.x_data = x_points
            # update kwargs to inital guess
            kwargs.update(self.livefit.result.init_values)
            self.update_plot()
        # Intentionally override LivePlot.event. Do not call super().

    def update_plot(self):
        self.current_line.set_data(self.x_data, self.y_data)
        # Rescale and redraw.
        # self.ax.relim(visible_only=True)
        # self.ax.autoscale_view(tight=True)
        # self.ax.figure.canvas.draw_idle()



class Plot_Options(QWidget, Ui_Plot_Options):
    def __init__(self, parent=None, ax=None, livePlot=None):
        super().__init__(parent)
        self.setupUi(self)
        self.ax = ax
        self.livePlot = livePlot
        self.livePlot.setup_done.connect(self.setup_table)
        self.checkBox_log_x.clicked.connect(self.set_log)
        self.checkBox_log_y.clicked.connect(self.set_log)
        self.checkBox_log_y2.clicked.connect(self.set_log)
        self.checkBox_use_abs_x.clicked.connect(self.set_log)
        self.checkBox_use_abs_y.clicked.connect(self.set_log)
        self.checkBox_use_abs_y2.clicked.connect(self.set_log)
        self.color_widges = []
        self.marker_widges = []
        self.linestyle_widges = []
        self.marker_dict = {}
        self.linestyle_dict = {}

    def setup_table(self):
        self.tableWidget.setColumnCount(4)
        self.tableWidget.setMinimumWidth(400)
        self.tableWidget.setHorizontalHeaderLabels(['Name', 'marker',
                                                    'color', 'linestyle'])
        self.tableWidget.verticalHeader().setHidden(True)
        for i, line in enumerate(self.ax.lines):
            if not self.marker_dict:
                self.marker_dict = {v: k for k, v in line.markers.items()}
                self.linestyle_dict = {''.join(v.split('_')[2:]): k for k, v in line.lineStyles.items()}
            self.tableWidget.insertRow(i)
            item = QTableWidgetItem(line.get_label())
            item.setFlags(item.flags() & ~Qt.ItemIsEditable)
            self.tableWidget.setItem(i, 0, item)
            markerwidge = QComboBox()
            markerwidge.addItems(self.marker_dict.keys())
            markerwidge.setCurrentText(line.markers[line.get_marker()])
            markerwidge.currentTextChanged.connect(lambda x, n=i: self.change_marker(n))
            self.marker_widges.append(markerwidge)
            self.tableWidget.setCellWidget(i, 1, markerwidge)
            colorwidge = QPushButton(line.get_color())
            colorwidge.clicked.connect(lambda x, n=i: self.change_color(n))
            self.color_widges.append(colorwidge)
            self.tableWidget.setCellWidget(i, 2, colorwidge)
            linestylewidge = QComboBox()
            linestylewidge.addItems(self.linestyle_dict.keys())
            print(line.get_linestyle)
            linestylewidge.setCurrentText(''.join(line.lineStyles[line.get_linestyle()].split('_')[2:]))
            linestylewidge.currentTextChanged.connect(lambda x, n=i: self.change_linestyle(n))
            self.linestyle_widges.append(linestylewidge)
            self.tableWidget.setCellWidget(i, 3, linestylewidge)
        self.tableWidget.resizeColumnsToContents()

    def change_linestyle(self, row):
        linestyle = self.linestyle_widges[row].currentText()
        self.ax.lines[row].set_linestyle(self.linestyle_dict[linestyle])
        self.ax.figure.canvas.draw_idle()

    def change_marker(self, row):
        marker = self.marker_widges[row].currentText()
        self.ax.lines[row].set_marker(self.marker_dict[marker])
        self.ax.figure.canvas.draw_idle()

    def change_color(self, row):
        color = QColorDialog.getColor()
        if color.isValid():
            self.color_widges[row].setText(color.name())
            line = self.ax.lines[row]
            line.set_color(color.name())
            self.ax.figure.canvas.draw_idle()

    def set_log(self):
        x = self.checkBox_log_x.isChecked()
        x_scale = 'log' if x else 'linear'
        self.checkBox_use_abs_x.setEnabled(x)
        y = self.checkBox_log_y.isChecked()
        y_scale = 'log' if y else 'linear'
        self.checkBox_use_abs_y.setEnabled(y)
        self.ax.set_xscale(x_scale)
        self.ax.set_yscale(y_scale)
        self.livePlot.use_abs = {'x': self.checkBox_use_abs_x.isChecked() and x,
                                 'y': self.checkBox_use_abs_y.isChecked() and y,
                                 'y2': self.checkBox_use_abs_y2.isChecked()}
        self.livePlot.update_plot()



class MultiLivePlot(LivePlot, QObject):
    new_data = pyqtSignal()
    setup_done = pyqtSignal()

    def __init__(self, ys=(), x=None, *, legend_keys=None, xlim=None, ylim=None,
                 ax=None, epoch='run', xlabel='', ylabel='', evaluator=None,
                 title='', stream_name='primary', do_plot=True, fitPlots=None,
                 **kwargs):
        LivePlot.__init__(self, y=ys[0], x=x, legend_keys=legend_keys,
                          xlim=xlim, ylim=ylim, ax=ax, epoch=epoch, **kwargs)
        QObject.__init__(self)
        self.use_abs = {'x': False, 'y': False, 'y2': False}
        self.__setup_lock = threading.Lock()
        self.__setup_event = threading.Event()
        self.eva = evaluator
        self.stream_name = stream_name
        self.desc = ''
        self.do_plot = do_plot
        self.fitPlots = fitPlots or []
        if isinstance(ys, str):
            ys = [ys]

        def setup():
            # Run this code in start() so that it runs on the correct thread.
            nonlocal ys, x, legend_keys, xlim, ylim, ax, epoch, kwargs, xlabel,\
                ylabel, title
            with self.__setup_lock:
                if self.__setup_event.is_set():
                    return
                self.__setup_event.set()
            if ax is None:
                fig, ax = plt.subplots()
            self.ax = ax

            if legend_keys is None:
                legend_keys = ys
            self.legend_keys = legend_keys
            if x is not None:
                self.x, *others = get_obj_fields([x])
            else:
                self.x = 'seq_num'
            self.ys = get_obj_fields(ys)
            self.ax.set_ylabel(ylabel or ys[0])
            self.ax.set_xlabel(xlabel or x or 'sequence #')
            if title:
                self.ax.set_title(title)
            if xlim is not None:
                self.ax.set_xlim(*xlim)
            if ylim is not None:
                self.ax.set_ylim(*ylim)
            self.ax.margins(.1)
            self.kwargs = kwargs
            self.lines = []
            self.legend = None
            # self.legend_title = " :: ".join([name for name in self.legend_keys])
            self._epoch_offset = None  # used if x == 'time'
            self._epoch = epoch

        self.__setup = setup
        self._epoch_offset = 0
        self.x_data = []
        self.y_data = {}
        self.y_names = ys
        self.ys = get_obj_fields(ys)
        for y in ys:
            self.y_data[y] = []
        self.current_lines = {}

    def start(self, doc):
        self.__setup()
        # The doc is not used; we just use the signal that a new run began.
        self._epoch_offset = doc['time']  # used if self.x == 'time'
        self.x_data = []
        self.y_data = {}
        for y in self.ys:
            self.y_data[y] = []
        # label = " :: ".join(
            # [str(doc.get(name, name)) for name in self.legend_keys])
        kwargs = ChainMap({'ls': 'None', 'marker': 'x'})
        self.current_lines = {}
        for i, y in enumerate(self.ys):
            try:
                self.current_lines[y], = self.ax.plot([], [],
                                                      label=self.legend_keys[i],
                                                      **kwargs)
            except Exception as e:
                print(e)
        self.lines.append(self.current_lines)
        legend = self.ax.legend(loc=0)
        try:
            # matplotlib v3.x
            self.legend = legend.set_draggable(True)
        except AttributeError:
            # matplotlib v2.x (warns in 3.x)
            self.legend = legend.draggable(True)
        for fit in self.fitPlots:
            fit.start(doc)
        self.setup_done.emit()

    def descriptor(self, doc):
        if doc['name'] == self.stream_name:
            self.desc = doc['uid']

    def clear_plot(self):
        self.x_data.clear()
        for y in self.y_data:
            self.y_data[y].clear()

    def event(self, doc):
        """Unpack data from the event and call self.update()."""
        # This outer try/except block is needed because multiple event
        # streams will be emitted by the RunEngine and not all event
        # streams will have the keys we want.
        # This inner try/except block handles seq_num and time, which could
        # be keys in the data or accessing the standard entries in every
        # event.
        if doc['descriptor'] != self.desc:
            return
        try:
            new_x = doc['data'][self.x]
        except KeyError:
            if self.x in ('time', 'seq_num'):
                new_x = doc[self.x]
            else:
                if not self.eva.is_to_date(doc['time']):
                    self.eva.event(doc)
                new_x = self.eva.eval(self.x)

        new_y = {}
        for y in self.ys:
            try:
                new_y[y] = doc['data'][y]
            except KeyError:
                if not self.eva.is_to_date(doc['time']):
                    self.eva.event(doc)
                new_y[y] = self.eva.eval(y)


        # Special-case 'time' to plot against against experiment epoch, not
        # UNIX epoch.
        if self.x == 'time' and self._epoch == 'run':
            new_x -= self._epoch_offset

        self.update_caches(new_x, new_y)
        for fit in self.fitPlots:
            fit.event(doc)
        self.update_plot()
        # super().event(doc)

    def update_caches(self, x, ys):
        for y in ys:
            self.y_data[y].append(ys[y])
        self.x_data.append(x)

    def update_plot(self):
        for y, line in self.current_lines.items():
            xdat = np.abs(self.x_data) if self.use_abs['x'] else self.x_data
            ydat = np.abs(self.y_data[y]) if self.use_abs['y'] else self.y_data[y]
            line.set_data(xdat, ydat)
        # Rescale and redraw.
        self.ax.relim(visible_only=True)
        self.ax.autoscale_view(tight=True)
        self.ax.figure.canvas.draw_idle()
        self.new_data.emit()

    def stop(self, doc):
        if not self.x_data:
            print('MultiLivePlot did not get any data that corresponds to the '
                  'x axis. {}'.format(self.x))
        for y in self.y_data:
            if not self.y_data[y]:
                print('MultiLivePlot did not get any data that corresponds to the '
                      'y axis. {}'.format(y))
            if len(self.y_data[y]) != len(self.x_data):
                print('MultiLivePlot has a different number of elements for x ({}) and'
                      'y ({}, {})'.format(len(self.x_data), len(self.y_data), y))
        for fit in self.fitPlots:
            fit.stop(doc)


if __name__ == '__main__':
    from bluesky import RunEngine
    from bluesky.plans import scan
    from ophyd.sim import motor, det

    motor.delay = 0.1

    def plan():
        for i in range(4, 5):
            yield from scan([det], motor, -5, 5, 3**i)

    RE = RunEngine()
    app = QApplication(sys.argv)
    # myapp = PlotWidget(run_engine=RE, x_name='motor', y_names=['det'], title='test', xlabel='aaaa', ylabel='bbbb')
    myapp = PlotWidget('motor', ['det', 'det**2', 'sin(motor)'])
    myapp.show()
    RE.subscribe(myapp.livePlot)
    RE(plan())
    sys.exit(app.exec_())