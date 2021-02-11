import os
import logging
import shutil
from pdf2image import convert_from_path
import pytesseract
import numpy as np
import cv2
import PyPDF2
import tempfile

import os_utils
import json_utils
import find_markers
from pageid import PageId, page_id_from_ocr

logger = logging.getLogger('medocr.'+__name__)


class Collection:
    def __init__(self, path):
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
            try:
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
            except KeyboardInterrupt:
                logger.warning('Keyboard interrupt in index loop. Stopped processing at page {}'.format(page_num))
                self._index[file_name][page_num] = None
                break
        self.write()

    def reorder_by_task(self, dest):
        # gather all pages for each task number
        pages_by_task_id = dict()
        for file_name, id_list in self._index.items():
            # logger.info('file name %s, id_list %s', file_name, id_list)
            for file_page, pid in enumerate(id_list):
                # logger.info('file page %s, pid %s', file_page, pid)
                page_id = PageId(pid)
                if page_id.task not in pages_by_task_id:
                    pages_by_task_id[page_id.task] = []
                pages_by_task_id[page_id.task].append((file_name, file_page, page_id))

        by_task = Collection.make_new_collection(dest)

        for tid, page_list in pages_by_task_id.items():
            file_dest = 'task{}.pdf'.format(tid)
            by_task._index[file_dest] = []

            open_infiles = dict()
            merger = PyPDF2.PdfFileMerger()
            for page_addr in page_list:
                file_name = page_addr[0]
                file_page = page_addr[1]
                page_id = page_addr[2]
                in_file_name = os.path.join(self._path, file_name)
                if in_file_name not in open_infiles:
                    open_infiles[in_file_name] = open(in_file_name, 'rb')
                merger.append(open_infiles[in_file_name], pages=(file_page, file_page + 1))
                by_task._index[file_dest].append(page_id.tuple())
            with open(os.path.join(dest, file_dest), 'wb') as out_file:
                merger.write(out_file)
            merger.close()
            by_task.write()
        return Collection(dest)

    def reorder_by_sheet(self, dest):
        raise NotImplementedError('The function reoder_by_sheet is not implemented yet')

    def validate(self):
        invalid = []
        unread = []
        duplicates = []
        pages_by_id = dict()

        for file_name, id_list in self._index.items():
            for page_num, page_id in enumerate(id_list):
                if page_id is None:
                    unread.append((file_name, page_id))
                if not page_id.is_valid:
                    pass


    def manual_label(self, file_name, page_num):
        pass

    def is_complete(self):
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
    def make_new_collection(path):
        if os.path.isdir(path):
            raise OSError('The directory already exists {}'.format(path))

        os.mkdir(path)
        json_utils.write_json(dict(), Collection.index_file(path))
        return Collection(path)

    @staticmethod
    def make_or_read_collection(path):
        if Collection.is_collection(path):
            logger.info('Reading existing collection %s', path)
            return Collection(path)

        logger.info('Creating the new collection %s', path)
        return Collection.make_new_collection(path)