import numpy as np
from ast import literal_eval
from PyQt5.QtWidgets import QMenu, QAction
from PyQt5.QtGui import QColor

from utility import simpleeval

from bluesky_widgets.models import utils

meas_preset = ''
dev_preset = ''
device_driver_path = ''

protocol_variables = {}
channels = {}
loop_step_variables = {}
devices = {}
dark_mode = False
evaluation_functions = simpleeval.DEFAULT_FUNCTIONS.copy()
evaluation_functions.update({'exp': np.exp,
                             'log': np.log,
                             'sqrt': np.sqrt,
                             'round': round,
                             'sin': np.sin,
                             'cos': np.cos,
                             'sinh': np.sinh,
                             'cosh': np.cosh,
                             'sinc': np.sinc,
                             'tan': np.tan,
                             'arctan': np.arctan,
                             'arcsin': np.arcsin,
                             'arccos': np.arccos,
                             'arcsinh': np.arcsinh,
                             'arccosh': np.arccosh,
                             'arctanh': np.arctanh})

evaluation_functions_names = {
    'randint()': 'randint(x) - random integer below x',
    'rand()': 'rand() - random float between 0 and 1',
    'round()': 'round(x) - round number to nearest integer',
    'exp()': 'exp(x) - exponential function of x',
    'sqrt()': 'sqrt(x) - square root of x',
    'log()': 'ln(x) - natural logarithm of x',
    'sin()': 'sin(x) - sine of x',
    'cos()': 'cos(x) - cosine of x',
    'tan()': 'tan(x) - tangent of x',
    'sinh()': 'sinh(x) - hyperbolic sine of x',
    'cosh()': 'cosh(x) - hyperbolic cosine of x',
    'tanh()': 'tanh(x) - hyperbolic tangent of x',
    'arctan()': 'arctan(x) - arcus tangent of x',
    'arcsin()': 'arcsin(x) - arcus sine of x',
    'arccos()': 'arccos(x) - arcus cosine of x',
    'arcsinh()': 'arcsinh(x) - area hyperbolic sine of x',
    'arccosh()': 'arccosh(x) - area hyperbolic cosine of x',
    'arctanh()': 'arctanh(x) - area hyperbolic tangent of x',
    'sinc()': 'sinc(x) - sinc function of x'
}

operator_names = {
    '+': 'add',
    '-': 'subtract',
    '/': 'devide',
    '*': 'multiply',
    '**': 'to the power of',
    '%': 'modulus',
    '==': 'equals',
    '<': 'less than',
    '>': 'greater than',
    '<=': 'less or equal',
    '>=': 'greater or equal',
}

def get_color(color, string=False):
    if color == 'red' or color == 'r':
        rgb = (255, 153, 153)
        if dark_mode:
            rgb = (153, 0, 0)
    elif color == 'green' or color == 'g':
        rgb = (153, 255, 153)
        if dark_mode:
            rgb = (0, 153, 0)
    else:
        rgb = (255, 255, 255)
        if dark_mode:
            rgb = (0, 0, 0)
    if string:
        return str(rgb)
    return QColor(*rgb)

def get_menus(connect_function):
    variable_menu = QMenu('Insert Variable')
    channel_menu = QMenu('Insert Channel-Value')
    function_menu = QMenu('Insert Function')
    operator_menu = QMenu('Insert Operator')
    channel_actions = []
    operator_actions = []
    actions = []
    function_actions = []
    for channel in sorted(channels, key=lambda x: x.lower()):
        action = QAction(channel)
        action.triggered.connect(lambda state, x=channel: connect_function(x))
        channel_actions.append(action)
    for variable in sorted(protocol_variables, key=lambda x: x.lower()):
        action = QAction(variable)
        action.triggered.connect(lambda state, x=variable: connect_function(x))
        actions.append(action)
    for variable in sorted(loop_step_variables, key=lambda x: x.lower()):
        action = QAction(variable)
        action.triggered.connect(lambda state, x=variable: connect_function(x))
        actions.append(action)
    for op in operator_names:
        action = QAction(f'{op}\t{operator_names[op]}')
        action.triggered.connect(lambda state, x=op: connect_function(x))
        operator_actions.append(action)
    for foo in sorted(evaluation_functions_names, key=lambda x: x.lower()):
        action = QAction(evaluation_functions_names[foo])
        action.triggered.connect(lambda state, x=foo: connect_function(x))
        function_actions.append(action)
    channel_menu.addActions(channel_actions)
    variable_menu.addActions(actions)
    operator_menu.addActions(operator_actions)
    function_menu.addActions(function_actions)
    menus = [channel_menu, variable_menu, operator_menu, function_menu]
    actions = [channel_actions, actions, operator_actions, function_actions]
    return menus, actions


def string_eval(s):
    names = {}
    names.update(protocol_variables)
    names.update(loop_step_variables)
    for channel in channels:
        names.update({channel: 0})
    return simpleeval.simple_eval(s, functions=evaluation_functions, names=names)

def check_eval(s):
    try:
        namespace = dict(utils._base_namespace)
        namespace.update(protocol_variables)
        namespace.update(loop_step_variables)
        for channel in channels:
            namespace.update({channel: 1})
        utils.call_or_eval_one(s, namespace)
        # string_eval(s)
        return True
    except Exception as e:
        print(e)
        return False

def get_data(s):
    """Returns the evaluated data of s."""
    if not s:
        return ''
    try:
        lit = literal_eval(s)
    except ValueError:
        return s
    except SyntaxError:
        return s
    return lit

def check_data_type(s):
    """Returns the datatype of the string-evaluation of s."""
    if not s:
        return ''
    try:
        lit = literal_eval(s)
    except ValueError:
        return 'String'
    except SyntaxError:
        return 'String'
    return str(type(lit))