import os
import logging


logger = logging.getLogger('medocr.'+__name__)


def mkdir_if_nonexistent(path):
    if not os.path.isdir(path):
        logger.debug('Making new directory %s', path)
        os.mkdir(path)


def make_directories_if_nonexistent(path):
    if not os.path.isdir(path):
        logger.debug('Recursively making new directory %s', path)
        os.makedirs(path)


def abs_path_switch(path, abs_path=True):
    if abs_path:
        return os.path.abspath(path)
    else:
        return path


class ChangedDirectory:

    def __init__(self, path):
        self._path = path
        self._origin = None

    def __enter__(self):
        self._origin = os.getcwd()
        logger.debug('Entering working directory %s', os.path.join(self._origin, self._path))
        os.chdir(self._path)
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        logger.debug('Changing working directory back to %s', self._origin)
        os.chdir(self._origin)
        return False
    
    def origin(self):
        return self._origin
    
    def current(self):
        return os.getcwd()
