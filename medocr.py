import os
import argparse
import logging
import sys
import tempfile
from pdf2image import convert_from_path
from PIL import Image
import pytesseract
import numpy as np


import os_utils
from defaultlogger import set_default_logging_behavior
logger = logging.getLogger('medocr.main')


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

    index_parser.add_argument('file', type=str, help='.pdf file containing scanned exams')

    args = main_parser.parse_args()

    try:
        if args.mode == 'index':
            os_utils.mkdir_if_nonexistent('work')
            dpi = 200
            images = convert_from_path(args.file, dpi=dpi, fmt='jpg', grayscale=True, output_folder='work')
            for img in images:
                inch_per_cm = 0.3937008
                footer_height = np.floor(1.5 * inch_per_cm * dpi)
                cropped = img.crop((0, img.height-footer_height, img.width, img.height))
                cropped.show()
                img_string = pytesseract.image_to_string(cropped)
                logger.info(img_string)
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
