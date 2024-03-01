#!/usr/bin/env python
#SETMODE 777

#----------------------------------------------------------------------------------------#
#------------------------------------------------------------------------------ HEADER --#

"""
:author:
    Nick Maclean

:synopsis:
    Basic logger with minimal formatting.
"""

#----------------------------------------------------------------------------------------#
#----------------------------------------------------------------------------- IMPORTS --#

# Built-In
from enum import Enum
import inspect
from time import localtime, strftime

#----------------------------------------------------------------------------------------#
#------------------------------------------------------------------------------- ENUMS --#


class Level(Enum):
    TRACE = 'Trace'
    INFO = 'Info'
    WARN = 'Warning'
    ERROR = 'Error'


#----------------------------------------------------------------------------------------#
#--------------------------------------------------------------------------- FUNCTIONS --#


def log(message, level=Level.INFO, step_back=2, width=120):
    trace = _build_trace(step_back)

    _log_to_console(message, level, trace, width)


def _log_to_console(message, level, trace, width):
    time_str = strftime("%H:%M:%S", localtime())

    # noinspection PyTypeChecker
    s = f'{time_str}  [{level.value.upper()}]  '
    indent = ''.join([' ' for _ in s])
    lines = []

    # wrap lines to fit width
    for c in message:
        s += c
        if c == '\n' or len(s) >= width:
            lines.append(s)
            s = indent

    # send to console
    lines.append(s)
    print('\n'.join(lines))

    if level == Level.TRACE or level == Level.INFO:
        return

    # show stack trace, for warnings/errors
    for frame in trace:
        file = frame['file']
        line = frame['line']
        function = frame['function']
        context = frame['context']
        print(f'  File "{file}", line {line}, in {function}')
        if context:
            print(f'    {context.lstrip()}')


def _build_trace(steps_back=2):
    stack = iter(inspect.stack())
    for i in range(steps_back):
        next(stack)

    return [{
                'file': frame.filename,
                'line': frame.lineno,
                'function': frame.function,
                'context': frame.code_context[0][:-1] if frame.code_context else None,
             }
            for frame in stack
    ]
