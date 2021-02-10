import os
import logging
import shutil
from pdf2image import convert_from_path
import pytesseract
import numpy as np
import cv2

import os_utils
import json_utils
import find_markers
from pageid import PageId, page_id_from_ocr

logger = logging.getLogger('medocr.'+__name__)


class Collection:
    def __init__(self, path=None):
        logger.info('Loading index %s', path)
        if not Collection.is_collection(path):
            raise OSError('The path {} does not point to a valid collection: '
                          'Either the directory does not exist, or it does not contain an index file'.format(path))

        self._path = path
        self._index_file = Collection.index_file(self._path)
        self._index = json_utils.read_json(self._index_file)


    def add_pdf(self, pdf, action='clear'):
        folder, file_name = os.path.split(pdf)
        file_is_in_index = file_name in self._index
        index_pdf = os.path.join(self._path, file_name)
        if file_is_in_index:
            logger.info('File %s already exists in the index')
            if action == 'ask':
                action = input('File %s already exists in the index. Select one of the following:\n'
                               '\t(clear) : Overwrite the current file\n'
                               '\t(resume) : Resume indexing the current file\n'
                               '\t(skip) : Do nothing for this file\n')
        else:
            action = 'clear'
        if action not in ['skip', 'clear', 'resume']:
            logger.warning('Action %s not understood.', action)
            action = 'skip'
        if action == 'skip':
            logger.info('Skipping file %s', pdf)
            return

        if action == 'clear':
            if file_is_in_index:
                logger.info('Overwriting file %s', pdf)
                os.remove(index_pdf)
            self._index[file_name] = []
            shutil.copyfile(pdf, index_pdf)

        if action == 'resume':
            raise NotImplementedError('Resuming indexing a file is not implemented yet.')

        work_folder = os.path.join(self._path, 'work')
        os_utils.mkdir_if_nonexistent(work_folder)
        os_utils.clear_files_with_extension(work_folder, 'jpg')
        dpi = 200
        logger.info('Converting the file "%s" to images', file_name)
        images = convert_from_path(index_pdf, dpi=dpi, fmt='jpg', grayscale=True, output_folder=work_folder)
        '''with tempfile.TemporaryDirectory() as temp_path:
            images_from_path = convert_from_path(args.file, output_folder=temp_path)'''
        logger.debug('finished converting')

        if action == 'clear':
            self._index[file_name] = [None for i in range(len(images))]
        for page_num, img in enumerate(images):
            if self._index[file_name][page_num] is not None:
                continue
            cv_image = cv2.cvtColor(np.array(img), cv2.COLOR_RGB2BGR)  # convert PIL image first to numpy array and then to the cv format for BGR color channels
            try:
                left_marker, right_marker, left_id = find_markers.findMarkers(cv_image)
                ocr_fields = find_markers.extract_ocr_fields(cv_image, left_marker, right_marker)
            except find_markers.MarkerException as mex:
                logger.info('Could not find the markers')
                logger.info(mex)
                self._index[file_name][page_num] = PageId()
            else:
                tesseract_options = r'--oem 3 --psm 6 outputbase digits'
                # tesseract_options = r'-c tessedit_char_blacklist=QO@~'
                ocr_strings = [pytesseract.image_to_string(f, config=tesseract_options) for f in ocr_fields]

                page_id = page_id_from_ocr(left_id, ocr_strings)
                success = page_id.is_valid()
                logger.info('Page %d,  Success : %s, %s', page_num, success, page_id)
                self._index[file_name][page_num] = page_id.tuple()

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
