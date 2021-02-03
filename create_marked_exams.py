import os
import copy
import PyPDF2
import argparse
import logging
import sys

from defaultlogger import set_default_logging_behavior
import os_utils

logger = logging.getLogger('medocr.create_marked_exams')


def validate_pdf_file_name(file_name):
    if not os.path.isfile(file_name):
        raise IOError('File {0} not found'.format(file_name))
    name, ext = os.path.splitext(file_name)
    if not ext == '.pdf': 
        raise ValueError('File {0} does not have the .pdf extension'.format(file_name))
    

def clear_pdfs(folder):
        logger.debug('Removing .pdf files in folder %s. ', folder)
        files = os.listdir(folder)
        for item in files:
            item_name, item_ext = os.path.splitext(item)
            if item_ext == '.pdf':
                os.remove(os.path.join(folder, item))


if __name__ == '__main__':
    set_default_logging_behavior(logfile='create_marked_exams')
    
    logger.debug('parsing args')
    parser = argparse.ArgumentParser(description='Generate exams that are marked with a unique identifier')
    parser.add_argument('exam', type=str, help='.pdf file of the exam')
    parser.add_argument('marks', type=str, help='.pdf file that contains the marks to be joined with the exam')
    parser.add_argument('--output', '-o', type=str, default=None, help='The folder for outputs')    
    args = parser.parse_args()
    
    try: 
        validate_pdf_file_name(args.exam)
        validate_pdf_file_name(args.marks)
        
        exam_name, ext = os.path.splitext(args.exam)
        
        if args.output is None:
            args.output = exam_name
        os_utils.mkdir_if_nonexistent(args.output)   
        clear_pdfs(args.output)

        with open(args.exam, 'rb') as exam_file: 
            with open(args.marks, 'rb') as marks_file:
                exam_pdf_reader = PyPDF2.PdfFileReader(exam_file)
                marks_pdf_reader = PyPDF2.PdfFileReader(marks_file)
                
                for idx in range(marks_pdf_reader.numPages): 
                    out_writer = PyPDF2.PdfFileWriter()
                    mark_page = marks_pdf_reader.getPage(idx)
                    for exam_page_number in range(exam_pdf_reader.numPages):
                        exam_page_original = exam_pdf_reader.getPage(exam_page_number)
                        exam_page = copy.copy(exam_page_original)
                        exam_page.mergePage(mark_page)
                        out_writer.addPage(exam_page)
                    out_file_name = '{0}_{1:03d}.pdf'.format(exam_name, idx)
                    with open(os.path.join(args.output, out_file_name), 'wb') as out_file:
                        out_writer.write(out_file)

    except Exception as ex:
        logger.critical('', exc_info=ex)
        sys.exit(1)
