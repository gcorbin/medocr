import logging


def set_default_logging_behavior(logfile):
    logger = logging.getLogger('medocr')

    logger.setLevel(logging.DEBUG)

    ch = logging.StreamHandler()
    ch.setLevel(logging.INFO)
    simple_format = logging.Formatter('%(levelname)s: %(message)s')
    ch.setFormatter(simple_format)
    logger.addHandler(ch)

    if logfile is not None:
        fh = logging.FileHandler('{0}.log'.format(logfile), mode='w')
        fh.setLevel(logging.DEBUG)
        detailed_format = logging.Formatter('%(asctime)s: %(levelname)s in %(name)s: %(message)s')
        fh.setFormatter(detailed_format)
        logger.addHandler(fh)