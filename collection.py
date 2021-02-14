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


def PIL_to_cv2(img):
    # convert PIL image first to numpy array and then to the cv format for BGR color channels
    return cv2.cvtColor(np.array(img), cv2.COLOR_RGB2BGR)

class Collection:
    def __init__(self, path):
        if not Collection.is_collection(path):
            raise OSError('The path {} does not point to a valid collection: '
                          'Either the directory does not exist, or it does not contain an index file'.format(path))

        self._path = path
        self._index_file = Collection.index_file(self._path)
        index_s = json_utils.read_json(self._index_file)
        self._index = Collection.index_to_page_id(index_s)
        self._examid = None
        for pid_list in self._index.values():
            if len(pid_list) > 0:
                self._examid = pid_list[0].exam
                break

    def add_pdf(self, pdf, action='clear'):
        folder, file_name = os.path.split(pdf)
        file_is_in_index = file_name in self._index
        index_pdf = os.path.join(self._path, file_name)
        if file_is_in_index:
            logger.info('File %s already exists in the index')
            if action == 'ask':
                action = input('File %s already exists in the index. Select one of the following:\n'
                               '\t(clear) : Overwrite the current file\n'
                               '\t(skip) : Do nothing for this file\n')
        else:
            action = 'clear'
        if action not in ['skip', 'clear']:
            logger.warning('Action %s not understood.', action)
            action = 'skip'
        if action == 'skip':
            logger.info('Skipping file %s', pdf)
            return

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

        self._index[file_name] = [None for i in range(len(images))]

        success = True
        marker_errors = 0
        continue_despite_marker_errors = False
        max_allowed_marker_errors = min(3, len(images))
        logger.info('max allowed marker errors = {}'.format(max_allowed_marker_errors))
        try:
            for page_num, img in enumerate(images):
                logger.info('Page number {}'.format(page_num + 1))
                cv_image = PIL_to_cv2(img)
                try:
                    left_marker, right_marker, left_id = find_markers.findMarkers(cv_image)
                    ocr_fields = find_markers.extract_ocr_fields(cv_image, left_marker, right_marker)
                    if self._examid is None:
                        self._examid = left_id
                    if self._examid != left_id:
                        raise find_markers.MarkerException('The marker id {} is different from the exam id {} of this collection'.format(left_id, self._examid))
                except find_markers.MarkerException as mex:
                    logger.warning(mex)
                    marker_errors += 1
                    self._index[file_name][page_num] = PageId()
                else:
                    tesseract_options = r'--oem 3 --psm 6 outputbase digits'
                    # tesseract_options = r'-c tessedit_char_blacklist=QO@~'
                    ocr_strings = [pytesseract.image_to_string(f, config=tesseract_options) for f in ocr_fields]

                    page_id = page_id_from_ocr(left_id, ocr_strings)
                    logger.info('Page id = %s', page_id)
                    self._index[file_name][page_num] = page_id

                if not continue_despite_marker_errors and marker_errors >= max_allowed_marker_errors:
                    logger.warning('Encountered at least {} pages with either unidentifiable markers or markers with'
                                   'the wrong id. The current exam id is {}.'.format(max_allowed_marker_errors, self._examid))

                    ans = input('Are you sure that you are reading the right pdf?\n'
                                'Enter "continue" to treat all further errors as image recognition errors\n'
                                'Enter "stop" if you do not want to enter this pdf to the collection\n'
                                'WARNING: Continuing with a wrong pdf will result in a corrupted index.\n'.format(self._examid))
                    while ans not in ['continue', 'stop']:
                        ans = input('Enter "stop" or "continue"\n')
                    if ans == 'continue':
                        logger.info('Continuing. Treating further marker errors as image recognition errors. ')
                        continue_despite_marker_errors = True
                    else:
                        logger.info('Stopping.')
                        success = False
                        continue_despite_marker_errors = False
                        break
        except Exception as ex:
            logger.critical('An unhandled exception occured during processing of the pdf {}'.format(file_name))
            os.remove(index_pdf)
            raise ex
        else:
            if success:
                logger.info('Successfully added the pdf to the collection.')
                self.write()
            else:
                logger.warning('The pdf was not be indexed completely and is not added to the collection.')
                self._index.pop(file_name)
                self.write()
                os.remove(index_pdf)

    def reorder_by(self, by, dest):
        if by not in ['sheet', 'task']:
            raise ValueError('The order criterion must be one of "sheet", "task"')
        # gather all pages for each task number
        pages_by_category = dict()
        for file_name, id_list in self._index.items():
            # logger.info('file name %s, id_list %s', file_name, id_list)
            for file_page, page_id in enumerate(id_list):
                # logger.info('file page %s, pid %s', file_page, pid)
                if by == 'sheet':
                    page_group = page_id.sheet
                else: # by == 'task':
                    page_group = page_id.task
                if page_group not in pages_by_category:
                    pages_by_category[page_group] = []
                pages_by_category[page_group].append((file_name, file_page, page_id))

        by_category = Collection.make_new_collection(dest)

        for tid, page_list in pages_by_category.items():
            file_dest = '{}{}.pdf'.format(by, tid)
            by_category._index[file_dest] = []

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
                by_category._index[file_dest].append(page_id)
            with open(os.path.join(dest, file_dest), 'wb') as out_file:
                merger.write(out_file)
            merger.close()
            by_category.write()
        return Collection(dest)

    def reorder_by_sheet(self, dest):
        raise NotImplementedError('The function reoder_by_sheet is not implemented yet')

    def validate(self):
        try:
            self.remove_corrupt_entries()
            self.label_invalid_entries_manually()
            duplicates = {('', 0):[]} # dummy duplicate dict to start the loop
            while len(duplicates.keys()) > 0:
                duplicates = self.find_duplicates()
                self.resolve_duplicates(duplicates)
            missing = self.find_missing_pages()
            if len(missing) > 0:
                logger.warning('The following pages are missing: %s', missing)
        except KeyboardInterrupt as ki:
            logger.warning('Keyboard interrupt during validation. Writing collection.')
            self.write()
            raise ki
        self.write()

    def remove_corrupt_entries(self):
        logger.info('Comparing index and file system.')
        remove_from_index = []
        remove_from_index_and_file_system = []
        for file_name, id_list in self._index.items():
            file_in_index = os.path.join(self._path, file_name)
            if os.path.isfile(file_in_index):
                with open(file_in_index, 'rb') as file:
                    pdf_reader = PyPDF2.PdfFileReader(file)
                    num_pages = pdf_reader.getNumPages()
                    if num_pages != len(id_list):
                        logger.warning('Index entry {}: Either the index entry or the corresponding file are corrupt: '
                                       'Pages in file = {}. Pages in index = {}'.format(file_name, num_pages, len(id_list)))
                        remove_from_index_and_file_system.append(file_name)
            else:
                remove_from_index.append(file_name)
                logger.warning('Index entry {}: The file belonging to the index entry is missing in the file system.'.format(file_name))

        # cannot remove keys from the dict during iteration
        logger.info('Removing the index entries for the missing files')
        for item in remove_from_index:
            logger.info('{}'.format(item))
            self._index.pop(item)
        logger.info('Removing the index entry and file for the corrupted entries')
        for item in remove_from_index_and_file_system:
            logger.info('{}'.format(item))
            self._index.pop(item)
            file_in_index = os.path.join(self._path, item)
            os.remove(file_in_index)

    def label_invalid_entries_manually(self):
        logger.info('Relabel invalid entries.')
        for file_name, id_list in self._index.items():
            for page_num, page_id in enumerate(id_list):
                if page_id is None or not page_id.is_valid():
                    self._index[file_name][page_num] = self.ask_for_label(file_name, page_num)

    def ask_for_label(self, file_name, page_num):
        PIL_img = convert_from_path(os.path.join(self._path, file_name), first_page=page_num+1, last_page=page_num+1, dpi=100, fmt='jpg', grayscale=True)
        img = PIL_to_cv2(PIL_img[0])
        window_name = 'File {}, page {}'.format(file_name, page_num)
        logger.info(window_name)
        cv2.namedWindow(window_name, cv2.WINDOW_NORMAL)
        cv2.resizeWindow(window_name, 600, 800)
        cv2.imshow(window_name, img)
        cv2.waitKey(1)

        pid = PageId()
        while not pid.is_valid():
            ans = input('Please enter the label for the shown page as "xxxx, yyyy, zzzz"\n')
            pid = page_id_from_ocr(self._examid, ans.split(','))
            logger.info('%s', pid)
        cv2.destroyWindow(window_name)
        return pid

    def find_duplicates(self):
        logger.info('Find and resolve duplicates.')
        duplicates = dict()
        pages_by_id = dict()

        for file_name, id_list in self._index.items():
            for page_num, page_id in enumerate(id_list):
                idt = page_id.tuple()
                # found a duplicate
                if idt in pages_by_id:
                    # this is a new duplicate
                    # create a new duplicate entry with the address of the current item and
                    # the address of the referenced item
                    if idt not in duplicates:
                        duplicates[idt] = [(file_name, page_num), pages_by_id[idt]]
                    # there are already more than two entries with the same page_id
                    # simply append the current item to the list of duplicates
                    else:
                        duplicates[idt].append((file_name, page_num))
                # no duplicate
                else:
                    pages_by_id[idt] = (file_name, page_num)
        return duplicates

    def resolve_duplicates(self, duplicates):
        for idt, duplist in duplicates.items():
            unchanged = []
            for page_addr in duplist:
                pid = self.ask_for_label(page_addr[0], page_addr[1])
                self._index[page_addr[0]][page_addr[1]] = pid
                if pid.tuple() == idt:
                    unchanged.append(page_addr)
            # we are in trouble, there is a true duplicate
            if len(unchanged) > 1:
                raise RuntimeError('File {}, page {}\nand file {}, page {}\nhave the same page id.\n'
                                   'Try to remove one of the files from the collection.'
                                   ''.format(unchanged[0][0], unchanged[0][1], unchanged[1][0], unchanged[1][1]))

    def find_missing_pages(self):
        logger.info('Find missing pages.')
        # find all unique sheet ids and page numbers
        sheets = set()
        pages = set()
        for id_list in self._index.values():
            for id in id_list:
                sheets.add(id.sheet)
                pages.add(id.page)

        # map from sheet ids and page numbers to rows and cols of an array
        sheet_rows = {s: i for i,s in enumerate(sheets)}
        page_cols = {p: i for i,p in enumerate(pages)}
        sheets_x_pages = np.zeros((len(sheet_rows), len(page_cols)))
        # find all combinations of sheet id and page numbers that exist in the index
        for id_list in self._index.values():
            for id in id_list:
                sheets_x_pages[sheet_rows[id.sheet], page_cols[id.page]] = 1
        # all other combinations are missing
        missing = [(s, p) for s in sheets for p in pages if sheets_x_pages[sheet_rows[s], page_cols[p]] == 0]
        # this algorithm will not report a page missing if it misses in each sheet
        return missing

    def is_complete(self):
        pass

    def write(self):
        index_s = Collection.index_to_serializable(self._index)
        json_utils.write_json(index_s, self._index_file)

    def __contains__(self, item):
        return item in self._index

    def remove(self, file):
        if os_utils.is_composite(file):
            raise RuntimeError('The name of the file to remove cannot be a path.')
        if file in self._index:
            self._index.pop(file)
            file_in_index = os.path.join(self._path, file)
            if os.path.isfile(file_in_index):
                os.remove(file_in_index)
            else:
                logger.warning('The file to be removed was listed in the index but not present in the file system.')
            self.write()
        else:
            logger.warning('The collection does not contain the file {}'.format(file))

    @staticmethod
    def index_to_serializable(index):
        index_s = dict()
        for file_name, id_list in index.items():
            index_s[file_name] = [pid.tuple() for pid in id_list]
        return index_s

    @staticmethod
    def index_to_page_id(index):
        index_p = dict()
        for file_name, id_list in index.items():
            index_p[file_name] = [PageId(s) for s in id_list]
        return index_p

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