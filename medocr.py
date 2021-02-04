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
import PyPDF2
import copy

import json_utils
import os_utils
from defaultlogger import set_default_logging_behavior

from pageid import PageId
logger = logging.getLogger('medocr.main')


def load_index(name, create_if_new=False):
    if os_utils.is_composite(name):
        raise ValueError('No paths are allowed as index names')

    index_file_name = os.path.join(name, 'index')

    if create_if_new and not os.path.isdir(name):
        logger.info('Creating the new index %s', name)
        os.mkdir(name)
        json_utils.write_json(dict(), index_file_name)

    if not os.path.isdir(name):
        raise NotADirectoryError('The index directory {} does not exist'.format(name))
    if not os.path.isfile(index_file_name):
        raise OSError('The directory {} exists, but it is not an index directory.'.format(name))

    logger.info('Working on index %s', name)
    index = json_utils.read_json(index_file_name)
    return index


def write_index(name, index):
    if os_utils.is_composite(name):
        raise ValueError('No paths are allowed as index names')

    index_file_name = os.path.join(name, 'index')
    if not os.path.isdir(name):
        raise NotADirectoryError('The index directory {} does not exist'.format(name))
    if not os.path.isfile(index_file_name):
        raise OSError('The directory {} exists, but it is not an index directory.'.format(name))
    json_utils.write_json(index, index_file_name)


def find_free_path(raw_path):
    path, prefix = os.path.split(raw_path)
    if path == '':
        path = '.'
    if not os.path.isdir(path):
        raise NotADirectoryError('The path {} does not exist'.format(path))

    full_path = os.path.join(path, prefix)
    number = 0
    while os.path.isdir(full_path):
        number += 1
        name = '{}_{:03d}'.format(prefix, number)
        full_path = os.path.join(path, name)
    return full_path


if __name__ == '__main__':
    set_default_logging_behavior(logfile='medocr')

    logger.debug('Parsing arguments')
    parent_parser = argparse.ArgumentParser()
    parent_parser.add_argument('index', type=str, help='The index to work on.')

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

    index_parser.add_argument('--file', '-f', type=str, default=None, help='.pdf file containing scanned exams')

    split_parser.add_argument('to',  type=str, help='folder containing the rearranged files')
    split_parser.add_argument('--prefix', type=str, default=None, help='prefix for files')

    args = main_parser.parse_args()

    try:
        if args.mode == 'index':
            index = load_index(args.index, create_if_new=True)

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
                tesseract_options = r'-c tessedit_char_blacklist=O@~'
                img_string = pytesseract.image_to_string(cropped, config=tesseract_options)
                page_id = PageId(img_string)
                success = page_id.is_valid()
                logger.info('Page %d,  Success : %s, %s, %s', page_num, success, page_id, PageId.tokenize_ocr_string(img_string))

                index[file_name][page_num] = page_id.tuple()
            write_index(args.index, index)

            '''with tempfile.TemporaryDirectory() as temp_path:
                images_from_path = convert_from_path(args.file, output_folder=temp_path)'''

        elif args.mode == 'split':
            index = load_index(args.index, create_if_new=False)

            dest = find_free_path(args.to)
            os_utils.mkdir_if_nonexistent(dest)

            if args.prefix is None:
                args.prefix = args.index

            # see which task numbers are in the index
            '''task_ids = set()
            for file_name, id_list in index.iteritems():
                for pid in id_list:
                    task_ids.add(pid.task)'''

            # gather all pages for each task number
            pages_by_task_id = dict()
            for file_name, id_list in index.items():
                #logger.info('file name %s, id_list %s', file_name, id_list)
                for file_page, pid in enumerate(id_list):
                    #logger.info('file page %s, pid %s', file_page, pid)
                    page_id = PageId(pid)
                    if page_id.task not in pages_by_task_id:
                        pages_by_task_id[page_id.task] = []
                    pages_by_task_id[page_id.task].append((file_name, file_page))

            print (pages_by_task_id)
            for tid, page_list in pages_by_task_id.items():
                out_writer = PyPDF2.PdfFileWriter()
                for page_addr in page_list:
                    file_name = page_addr[0]
                    file_page = page_addr[1]
                    #pid = page_addr[2]
                    with open(os.path.join(args.index, file_name), 'rb') as in_file:
                        pdf_reader = PyPDF2.PdfFileReader(in_file)
                        pdf_page = pdf_reader.getPage(file_page)
                        out_writer.addPage(pdf_page)
                        with open(os.path.join(dest, '{}_task{}.pdf'.format(args.prefix, tid)), 'wb') as out_file:
                            out_writer.write(out_file)
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
