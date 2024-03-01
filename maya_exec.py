#!/usr/bin/env python
# SETMODE 777

#----------------------------------------------------------------------------------------#
#------------------------------------------------------------------------------ HEADER --#

"""
:author:
    Nick Maclean

:synopsis:
    Maya specific AppExecuters
"""

#----------------------------------------------------------------------------------------#
#----------------------------------------------------------------------------- IMPORTS --#

# Built-In
import os
from subprocess import Popen
from tempfile import NamedTemporaryFile

# Internal
from app_exec import AppExecuter

#----------------------------------------------------------------------------------------#
#----------------------------------------------------------------------------- CLASSES --#


class MayabatchExecuter(AppExecuter):
    NAME_EXE = 'mayabatch.exe'

    @classmethod
    def _get_exe_path(cls, name_exe: str) -> str:
        path = super()._get_exe_path(name_exe)

        # try hard-coded path to mayabatch, if the PATH variable has not been injected
        # this should only be the case when this interpreter is not Maya's embedded one
        return path if path else 'C:/Program Files/Autodesk/Maya2023/bin\mayabatch.exe'

    def run(self, path_maya_file: str = None, command: str = None, func: str = None,
            *args, **kwargs) -> Popen:
        """
        Opens mayabatch.exe and runs the provided python code. One of command, path_py,
        or func must be provided.

        :param path_maya_file: (optional) maya file to work with
        :type: str

        :param command: string of python code to run
        :type: str

        :param func: a python function to run
        :type: (absolute path to py module, name of function)

        :param args:
        :param kwargs:

        :return: the resulting subprocess
        :type: Popen
        """
        # validate maya file
        if path_maya_file and not os.path.isfile(path_maya_file):
            return None

        if not command and not func:
            return None

        # make a file to write errors to
        # python errors in mayabatch are sent to stdout, so we need to do some trickery
        # to extract errors from it
        file_errors = NamedTemporaryFile(delete=False)
        path_errors = file_errors.name
        file_errors.close()

        # construct command to run the provided function
        if func:
            command = f'from {func[0]} import {func[1]}; {func[1]}()'

        # write python command to a temp file for mayabatch to run
        # this will help prevent issues caused by running arbitrary py code in mel
        file_py = NamedTemporaryFile('w', delete=False)
        path_py = file_py.name

        # inject cleanup code and environment setup
        command = '\n'.join([
            f'import utd_menu',
            f'try:',
            f'    {command}',
            f'except Exception as e:',
            f'    import traceback',
            f'    with open(r\'{path_errors}\', \'w\') as file:',
            f'        file.write(traceback.format_exc())',
            f'finally:',
            f'    import os',
            f'    os.remove(r\'{path_py}\')',
        ])

        # save code
        file_py.write(command)
        file_py.close()

        # run mayabatch!
        path_py = path_py.replace('\\', '\\\\')
        command = f'python(\"exec(open(r\'{path_py}\', \'r\').read())\")'
        if path_maya_file:
            result = super().run(file=path_maya_file, command=command, *args, *kwargs)
        else:
            result = super().run(command=command, *args, *kwargs)

        # store path to text file errors are directed to
        if result:
            result.path_errors = path_errors

        # the temp files are only deleted if a subprocess is actually started, so we need
        # to manually delete them if its fails
        if not result:
            if os.path.isfile(path_py):
                os.remove(path_py)
            if os.path.isfile(path_errors):
                os.remove(path_errors)

        return result

    @classmethod
    def notify(cls, process: Popen):
        # check tempfile for any errors
        with open(process.path_errors, 'r') as file:
            errors = file.read()
        os.remove(process.path_errors)

        # log result
        s = 'subprocess: "{process.executable}" {" ".join(process.args)}'
        if errors:
            print(f'Failed {s}')
            print(errors)
        else:
            print(f'Finished {s}')

        # notify user with GUI
        # be careful, this is called by cls._watch_processes from another thread
        # you can confirm this with threading.current_thread() is threading.main_thread()
        # you can use evalDefered to run gui on the main thread.
