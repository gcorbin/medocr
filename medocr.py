import os
import argparse
import logging
import sys
import os_utils
from defaultlogger import set_default_logging_behavior

from collection import Collection
logger = logging.getLogger('medocr.main')


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
    parent_parser.add_argument('index', help='The index to work on.')

    main_parser = argparse.ArgumentParser(description='Index pdf files by OCR marks '
                                                      'and rearrange the pages accordingly.')
    subparsers = main_parser.add_subparsers(dest='mode', title='Subcommands',
                                            description='Select one of the following operations: ')
    add_parser = subparsers.add_parser('add', parents=[parent_parser], conflict_handler='resolve',
                                         help='Create an index from OCR marks.')
    split_parser = subparsers.add_parser('split', parents=[parent_parser], conflict_handler='resolve',
                                         help='Split individual exams and rearrange by task number.')
    merge_parser = subparsers.add_parser('merge', parents=[parent_parser], conflict_handler='resolve',
                                         help='Merge back into the individual exams.')
    validate_parser = subparsers.add_parser('validate', parents=[parent_parser], conflict_handler='resolve',
                                         help='Validate the collection.')
    remove_parser = subparsers.add_parser('remove', parents=[parent_parser], conflict_handler='resolve',
                                          help='Remove a file from the collection.')

    add_parser.add_argument('file', help='The .pdf file containing scanned exams.')
    remove_parser.add_argument('file', help='.The name of the file to be removed.')

    split_parser.add_argument('to', help='folder containing the rearranged files')

    args = main_parser.parse_args()

    try:
        if args.mode == 'add':
            collection = Collection.make_or_read_collection(args.index)
            os_utils.validate_file_name(args.file, 'pdf')
            collection.add_pdf(args.file, 'ask')
        elif args.mode == 'remove':
            collection = Collection(args.index)
            collection.remove(args.file)
        elif args.mode == 'split':
            collection = Collection(args.index)
            dest = find_free_path(args.to)
            by_task = collection.reorder_by_task(dest)
        elif args.mode == 'merge':
            collection = Collection(args.index)
            dest = find_free_path(args.to)
            by_sheet = collection.reorder_by_sheet(dest)
        elif args.mode == 'validate':
            collection = Collection(args.index)
            collection.validate()
        else:
            # should never happen, because the argparse module asserts that only the existing choices are possible
            logger.error('Unrecognized subcommand %s', args.mode)
            main_parser.print_help()

    except Exception as ex:
        logger.critical('', exc_info=ex)
        sys.exit(1)
    sys.exit(0)
