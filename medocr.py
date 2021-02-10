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
import cv2
import imutils #for contours

import json_utils
import os_utils
import find_markers
from defaultlogger import set_default_logging_behavior

from pageid import PageId, page_id_from_ocr
from collection import Collection
logger = logging.getLogger('medocr.main')


'''def load_index(name, create_if_new=False):
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
    json_utils.write_json(index, index_file_name)'''


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


# get grayscale image
def get_grayscale(image):
    return cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)

# noise removal
def remove_noise(image):
    return cv2.medianBlur(image, 5)

# thresholding
def thresholding(image):
    return cv2.threshold(image, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)[1]

#skew correction
def deskew(image):
    bw = thresholding(get_grayscale(image))
    coords = np.column_stack(np.where(bw < 255))
    center, dimensions, angle= cv2.minAreaRect(coords)
    if angle < -45:
        angle = -(90 + angle)
    else:
        angle = -angle
    logger.info('rect center {}, dimensions {},  angle = {}'.format(center, dimensions, angle))
    (h, w) = image.shape[:2]
    im_center = (w // 2, h // 2)
    M = cv2.getRotationMatrix2D(im_center, angle, 1.0)
    crop_border = 5
    rotated = cv2.warpAffine(image, M, (w, h), flags=cv2.INTER_CUBIC, borderMode=cv2.BORDER_REPLICATE)
    crop_h = slice(max(int(np.floor(center[0]-dimensions[0]/2.-crop_border)), 0),
                   min(int(np.ceil (center[0]+dimensions[0]/2.+crop_border)), h-1))
    crop_w = slice(max(int(np.floor(center[1]-dimensions[1]/2.-crop_border)), 0),
                   min(int(np.ceil (center[1]+dimensions[1]/2.+crop_border)), w-1))
    #crop_w = slice(int(np.floor(center[1] - dimensions[1] / 2.)), int(np.ceil(center[1] + dimensions[1] / 2.)))
    cropped = rotated[crop_h, crop_w]
    return cropped


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
            #index = load_index(args.index, create_if_new=True)
            collection = Collection.make_collection(args.index)

            if args.file is None:
                logger.info('No file given, doing nothing.')
                sys.exit(0)

            os_utils.validate_file_name(args.file, 'pdf')
            collection.add_pdf(args.file, 'ask')
            collection.write()

        elif args.mode == 'split':
            '''index = load_index(args.index, create_if_new=False)

            dest = find_free_path(args.to)
            os_utils.mkdir_if_nonexistent(dest)

            if args.prefix is None:
                args.prefix = args.index

            # gather all pages for each task number
            pages_by_task_id = dict()
            for file_name, id_list in index.items():
                # logger.info('file name %s, id_list %s', file_name, id_list)
                for file_page, pid in enumerate(id_list):
                    # logger.info('file page %s, pid %s', file_page, pid)
                    page_id = PageId(pid)
                    if page_id.task not in pages_by_task_id:
                        pages_by_task_id[page_id.task] = []
                    pages_by_task_id[page_id.task].append((file_name, file_page, page_id))

            # print (pages_by_task_id)

            new_index = dict()
            for tid, page_list in pages_by_task_id.items():
                file_dest = '{}_task{}.pdf'.format(args.prefix, tid)
                new_index[file_dest] = []

                open_infiles = dict()
                merger = PyPDF2.PdfFileMerger()
                for page_addr in page_list:
                    file_name = page_addr[0]
                    file_page = page_addr[1]
                    page_id = page_addr[2]
                    in_file_name = os.path.join(args.index, file_name)
                    if in_file_name not in open_infiles:
                        open_infiles[in_file_name] = open(in_file_name, 'rb')
                    merger.append(open_infiles[in_file_name], pages=(file_page, file_page+1))
                    new_index[file_dest].append(page_id.tuple())
                with open(os.path.join(dest, file_dest), 'wb') as out_file:
                    merger.write(out_file)
                merger.close()
                json_utils.write_json(new_index, os.path.join(dest, 'index'))'''
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
