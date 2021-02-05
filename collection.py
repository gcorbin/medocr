import os
import logging

import os_utils
import json_utils

logger = logging.getLogger('medocr.'+__name__)


class Collection:
    def __init__(self, path=None):
        logging.info('Loading index %s', path)
        if not Collection.is_collection(path):
            raise OSError('The path {} does not point to a valid collection: '
                          'Either the directory does not exist, or it does not contain an index file'.format(path))

        self._path = path
        self._index_file = Collection.index_file(self._path)
        self._index = json_utils.read_json(self._index_file)

    def add_pdf(self):
        pass
    
    def write(self):
        json_utils.write_json(self._index, self._index_file)

    @staticmethod
    def is_collection(path):
        if not os.path.isdir(path):
            return False
        return os.path.isfile(Collection.index_file(path))

    @staticmethod
    def is_occupied_dir(path):
        if os.path.isdir(path):
            return not os.path.isfile(Collection.index_file(path))
        return False

    @staticmethod
    def index_file(path):
        return os.path.join(path, 'index')

    @staticmethod
    def make_collection(path):
        if Collection.is_collection(path):
            return Collection(path)

        logger.info('Creating the new index %s', path)

        if Collection.is_occupied_dir(path):
            raise OSError('The directory {} already exists, but does not contain an index file'.format(path))

        os.mkdir(path)
        json_utils.write_json(dict(), Collection.index_file(path))
        return Collection(path)
