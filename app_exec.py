#!/usr/bin/env python
# SETMODE 777

#----------------------------------------------------------------------------------------#
#------------------------------------------------------------------------------ HEADER --#

"""
:author:
    Nick Maclean

:synopsis:
    Base system for running and managing subprocesses.
"""

#----------------------------------------------------------------------------------------#
#----------------------------------------------------------------------------- IMPORTS --#

# Built-In
import os
import shutil
from subprocess import Popen, DEVNULL
from threading import Thread
from time import sleep
from queue import Queue

#----------------------------------------------------------------------------------------#
#--------------------------------------------------------------------------- FUNCTIONS --#


class AppExecuter(object):
    """
    Extendable system for running and managing subprocesses. Although this class can be
    used directly to run a subprocess, you probably want to derrive from this and modify
    child.run()
    """
    NAME_EXE: str = None
    PROCESSES: Queue[Popen] = Queue()
    WATCHER: Thread = None

    def __init__(self, name_exe=None, path_exe=None):
        if name_exe:
            self.NAME_EXE = name_exe
        self.path_exe: str = path_exe

    @classmethod
    def _get_exe_path(cls, name_exe: str) -> str:
        """
        Gets the absolute path to the exe on path.

        :param name_exe: name of an exe (does not have to have the extension)
        :type: str

        :return: absolute path to .exe
        :type: str
        """
        return shutil.which(name_exe)

    @classmethod
    def _watch_processes(cls, queue: Queue[Popen]):
        """
        Periodically checks the queue of processes. Notifies the user of the process
        results, when each one completes. The loop terminates if there are no more
        processes to check.

        :param queue: thread-safe queue of processes to watch
        :type: Queue[Popen]
        """
        while True:
            sleep(0.5)

            # check processes in queue
            running = []
            while not queue.empty():
                process = queue.get()

                # ignore processes that are still running
                process.poll()
                if process.returncode is None:
                    running.append(process)
                    continue

                # notify user of success or failure
                cls.notify(process)

            # if there are no more subprocesses to manage, shut down the thread
            if not running:
                break

            # return processes that are still running
            for process in running:
                queue.put(process)

    def validate(self) -> bool:
        """
        Lazily collects and validates information necessary to run this executer.

        :return: True if self is valid
        :type: bool
        """
        # validate exe path
        if not self.path_exe:
            self.path_exe = self._get_exe_path(self.NAME_EXE)
            if not os.path.isfile(self.path_exe):
                return False

        return True

    def run(self, *args, **kwargs) -> Popen:
        """
        Executes this task in a subprocess and send notification upon completion.

        :param args: args passed to subprocess
        :param kwargs: kwargs passed to subprocess

        :return: the resulting subprocess
        :type: Popen
        """
        if not self.validate():
            return None

        # start subprocess
        args = list(args)
        for kwarg in kwargs:
            args.append(f'-{kwarg}')
            args.append(kwargs[kwarg])

        process = Popen(args, executable=self.path_exe, stdout=DEVNULL)
        process.executable = self.path_exe

        # lazy create the thread
        if not self.WATCHER or not self.WATCHER.is_alive():
            self.WATCHER = Thread(target=self._watch_processes, args=(self.PROCESSES, ))
            self.WATCHER.start()

        # add process to the queue being watched
        self.PROCESSES.put(process)
        return process

    @classmethod
    def notify(cls, process: Popen):
        """
        Notifies user that the provided process has been completed. It may or may not have
        been successful.

        :param process: subprocess that has been terminated
        :type: subprocess.Popen
        """
        # log result
        result, errors = process.communicate()
        print(f'Finished subprocess: "{process.executable}" {" ".join(process.args)}')
        print(f'  {errors}')

        # notify user with GUI
        # be careful, this is called by cls._watch_processes from another thread
        # you can confirm this with threading.current_thread() is threading.main_thread()
        # APIs or GUI libraries you're using may not be thread safe
        # for Maya, you can use evalDefered to run a function on the main thread.
