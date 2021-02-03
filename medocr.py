import os
import argparse
import logging
import sys

from defaultlogger import set_default_logging_behavior
logger = logging.getLogger('medocr.main')


if __name__ == '__main__':
    set_default_logging_behavior(logfile='medocr')

    logger.debug('Parsing arguments')
    parent_parser = argparse.ArgumentParser()

    main_parser = argparse.ArgumentParser(description='Index pdf files by OCR marks and rearrange the pages accordingly')
    subparsers = main_parser.add_subparsers(dest='mode', required=True,
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
            pass
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
