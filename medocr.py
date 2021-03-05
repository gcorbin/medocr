import os
import argparse
import logging
import sys
import os_utils
import time
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


def find_most_recent_log_number(path):
    logfiles = [name_ext for name_ext in os.listdir(path) if name_ext.startswith('medocr') and name_ext.endswith('.log')]
    most_recent_number = 0
    most_recent_time = 0  # start of the epoch
    for name_ext in logfiles:
        name, ext = os.path.splitext(name_ext)
        tmp = name.split('-')
        if len(tmp) != 2:
            continue
        number_string = tmp[1]
        try:
            number = int(number_string)
        except ValueError:
            continue
        modification_time = os.stat(os.path.join(path, name_ext)).st_mtime
        if modification_time > most_recent_time:
            most_recent_time = modification_time
            most_recent_number = number
    return most_recent_number


if __name__ == '__main__':
    prev_log_number = find_most_recent_log_number('.')
    log_number = (prev_log_number % 5) + 1
    set_default_logging_behavior(logfile='medocr-{:d}'.format(log_number))

    logger.debug('Parsing arguments')
    parent_parser = argparse.ArgumentParser()

    main_parser = argparse.ArgumentParser(description='This program helps distributing scans of written exams to the correctors.\n'
                                                      'To create an index of pages, it looks for special identifiers that have to printed on every page.\n'
                                                      'Pages can be grouped by task id (for the correctors) or by sheet id (for the students)\n')

    main_parser.add_argument('collection', help='The collection to work on.')

    subparsers = main_parser.add_subparsers(dest='mode', title='Subcommands',
                                            description='Select one of the following operations:')
    add_parser = subparsers.add_parser('add', parents=[parent_parser], conflict_handler='resolve',
                                       help='Add a .pdf with marked pages into the collection.')
    remove_parser = subparsers.add_parser('remove', parents=[parent_parser], conflict_handler='resolve',
                                          help='Remove a file from the collection.')
    order_parser = subparsers.add_parser('order-by', parents=[parent_parser], conflict_handler='resolve',
                                         help='Order the pages in the files by [sheet, task].')
    validate_parser = subparsers.add_parser('validate', parents=[parent_parser], conflict_handler='resolve',
                                            help='Validate the collection.')

    add_parser.add_argument('file', help='The .pdf file to be added.')
    remove_parser.add_argument('file', help='The file to be removed from the collection.')

    order_parser.add_argument('by', choices=['sheet', 'task'], help='The order criterion.')
    order_parser.add_argument('--to', help='The folder containing the rearranged collection.', default=None)

    validate_parser.add_argument('--extra-pages', '-xp', nargs='+', type=int, default=(),
                                 help='Exclude extra pages from the check for missing pages.')
    args = main_parser.parse_args()

    try:
        if args.mode == 'add':
            collection = Collection.make_or_read_collection(args.collection)
            os_utils.validate_file_name(args.file, 'pdf')
            collection.add_pdf(args.file, 'ask')
        elif args.mode == 'remove':
            collection = Collection(args.collection)
            collection.remove(args.file)
        elif args.mode == 'order-by':
            collection = Collection(args.collection)

            if args.to is None:
                parent_folder, collection_name = os.path.split(os.path.normpath(os.path.realpath(args.collection)))
                dest = os.path.join(parent_folder, '{}_by_{}'.format(collection_name, args.by))
            else:
                dest = args.to
            dest = find_free_path(dest)
            new_collection = collection.reorder_by(args.by, dest)
        elif args.mode == 'validate':
            collection = Collection(args.collection)
            collection.validate(args.extra_pages)
        else:
            main_parser.print_usage()

    except Exception as ex:
        logger.critical('', exc_info=ex)
        sys.exit(1)
    sys.exit(0)
