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


def validate_file_name(file_name, extension=None):
    if not os.path.isfile(file_name):
        raise IOError('File {0} not found'.format(file_name))
    if extension is not None:
        name, ext = os.path.splitext(file_name)
        if not ext == '.'+extension:
            raise ValueError('File {0} does not have the .{1} extension'.format(file_name, extension))


def clear_files_with_extension(folder, extension):
    logger.debug('Removing .%s files in folder %s. ', extension, folder)
    files = os.listdir(folder)
    for item in files:
        item_name, item_ext = os.path.splitext(item)
        if item_ext == '.'+extension:
            os.remove(os.path.join(folder, item))