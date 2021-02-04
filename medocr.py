import os
import argparse
import logging
import sys
import tempfile
from pdf2image import convert_from_path
from PIL import Image
import pytesseract
import numpy as np
import shutil

import json_utils
import os_utils
from defaultlogger import set_default_logging_behavior
logger = logging.getLogger('medocr.main')


class PageId:
    def __init__(self, data=None):
        self.exam = None
        self.task = None
        self.page = None
        if data is not None:
            if isinstance(data, str):
                self.init_from_ocr_string(data)
            elif isinstance(data, tuple):
                if len(data) != 3:
                    raise ValueError('A PageId object needs 3 values to be constructed.')
                self.exam = data[0]
                self.task = data[1]
                self.page = data[2]
            else:
                raise TypeError('A PageId needs a tuple or a string to be constructed.')

    def tuple(self):
        return self.exam, self.task, self.page

    def is_valid(self):
        return self.exam is not None \
               and self.task is not None\
               and self.page is not None

    def __str__(self):
        return 'Klausur {}, Aufgabe {}, Seite {}'.format(self.exam, self.task, self.page)

    @staticmethod
    def tokenize_ocr_string(data):
        ocr_string = ''.join(data.split()).upper()
        return ocr_string.split('-')

    def init_from_ocr_string(self, data):
        ocr_tokens = PageId.tokenize_ocr_string(data)

        for token in ocr_tokens:
            if token.startswith('KLAUSUR'):
                subtokens = token.split('KLAUSUR')
                number = subtokens[1]
                if number.isdigit():
                    self.exam = int(number)
            elif token.startswith('AUFGABE'):
                subtokens = token.split('AUFGABE')
                number = subtokens[1]
                if number.isdigit():
                    self.task = int(number)
            elif token.startswith('DECKBLATT'):
                self.task = 0
            elif token.startswith('SEITE'):
                subtokens = token.split('SEITE')
                self.page = subtokens[1]
            elif token.startswith('EXTRASEITE'):
                self.page = 0
            elif token == '':
                pass
            else:
                pass


if __name__ == '__main__':
    set_default_logging_behavior(logfile='medocr')

    logger.debug('Parsing arguments')
    parent_parser = argparse.ArgumentParser()

    main_parser = argparse.ArgumentParser(description='Index pdf files by OCR marks and rearrange the pages accordingly')
    subparsers = main_parser.add_subparsers(dest='mode',
                                            title='Subcommands',
                                            description='Select one of the following operations: ')
    index_parser = subparsers.add_parser('index', parents=[parent_parser], conflict_handler='resolve',
                                         help='Create an index from OCR marks')
    split_parser = subparsers.add_parser('split', parents=[parent_parser], conflict_handler='resolve',
                                         help='Split individual exams and rearrange by task number')
    merge_parser = subparsers.add_parser('merge', parents=[parent_parser], conflict_handler='resolve',
                                         help='Merge back into the individual exams')

    index_parser.add_argument('index', type=str, help='The index to work on. If it does not exist, create it.')
    index_parser.add_argument('--file', '-f', type=str, default=None, help='.pdf file containing scanned exams')

    args = main_parser.parse_args()

    try:
        if args.mode == 'index':
            index_file_name = os.path.join(args.index, 'index')

            if not os.path.isdir(args.index):
                logger.info('Creating the new index %s', args.index)
                os.mkdir(args.index)
                json_utils.write_json(dict(), index_file_name)

            if not os.path.isfile(index_file_name):
                logger.critical('The directory %s exists, but it is not an index directory.')
                sys.exit(1)

            logger.info('Working on index %s', args.index)
            index = json_utils.read_json(index_file_name)

            if args.file is None:
                logger.info('No file given, doing nothing.')
                sys.exit(0)

            os_utils.validate_file_name(args.file, 'pdf')
            folder, file_name = os.path.split(args.file)
            file_in_index = os.path.join(args.index, file_name)
            if file_name in index:
                logger.info('File %s already exists in the index')
                ans = input('File %s already exists in the index. Select one of the following:\n'
                      '\t(clear) : Overwrite the current file\n'
                      '\t(resume) : Resume indexing the current file\n'
                      '\t(skip) : Do nothing for this file\n')
                if ans == 'clear':
                    index[file_name] = []
                    os.remove(file_in_index)
                    shutil.copyfile(args.file, file_in_index)
                elif ans == 'resume':
                    raise NotImplementedError('Resuming indexing a file is not implemented yet.')
                elif ans == 'skip':
                    logger.info('Skipping file %s', file_name)
                    sys.exit(0)
                else:
                    logger.warning('Input %s not understood.', ans)
                    logger.info('Skipping file %s', file_name)
            else:
                index[file_name] = []
                shutil.copyfile(args.file, file_in_index)


            work_folder = os.path.join(args.index, 'work')
            os_utils.mkdir_if_nonexistent(work_folder)
            os_utils.clear_files_with_extension(work_folder, 'jpg')
            dpi = 200
            logger.info('Converting the file "%s" to images', file_name)
            images = convert_from_path(file_in_index, dpi=dpi, fmt='jpg', grayscale=True, output_folder=work_folder)
            logger.debug('finished converting')

            index[file_name] = [None for i in range(len(images))]
            #TODO: clear the work directory or use a temporary
            for page_num, img in enumerate(images):
                inch_per_cm = 0.3937008
                footer_height = np.floor(2.5 * inch_per_cm * dpi)
                cropped = img.crop((0, img.height-footer_height, img.width, img.height))
                #cropped.show()
                img_string = pytesseract.image_to_string(cropped)
                page_id = PageId(img_string)
                success = page_id.is_valid()
                logger.info('Page %d,  Success : %s, %s, %s', page_num, success, page_id, PageId.tokenize_ocr_string(img_string))

                index[file_name][page_num] = page_id.tuple()
            json_utils.write_json(index, index_file_name)

            '''with tempfile.TemporaryDirectory() as temp_path:
                images_from_path = convert_from_path(args.file, output_folder=temp_path)'''

        elif args.mode == 'split':
            logger.warning('The subcommand "split" is not implemented yet. Doing nothing')
        elif args.mode == 'merge':
            logger.warning('The subcommand "merge" is not implemented yet. Doing nothing')
        else:
            # should never happen, because the argparse module asserts that only the existing choices are possible
            logger.error('Unrecognized subcommand %s', args.mode)
            main_parser.print_help()

    except Exception as ex:
        logger.critical('', exc_info=ex)
        sys.exit(1)
    sys.exit(0)
