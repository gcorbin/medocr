import os
import copy
import PyPDF2
import argparse
import logging

from defaultlogger import set_default_logging_behavior
logger = logging.getLogger('medocr.create_marked_exams')

import os_utils


def validate_pdf_file_name(file_name):
    if not os.path.isfile(file_name):
        raise IOError('File {0} not found'.format(file_name))
    name, ext = os.path.splitext(file_name)
    if not ext == '.pdf': 
        raise ValueError('File {0} does not have the .pdf extension'.format(file_name))


if __name__ == '__main__':
    set_default_logging_behavior(logfile='create_marked_exams')
    
    logger.debug('parsing args')
    parser = argparse.ArgumentParser(description='Generate exams that are marked with a unique identifier')
    parser.add_argument('exam', type=str, help='.pdf file of the exam')
    parser.add_argument('marks', type=str, help='.pdf file that contains the marks to be joined with the exam')
    parser.add_argument('--output', '-o', type=str, default=None, help='The folder for outputs')    
    args = parser.parse_args()
    
    validate_pdf_file_name(args.exam)
    validate_pdf_file_name(args.marks)
    
    exam_name, ext = os.path.splitext(args.exam)
    
    if args.output is None:
        args.output = exam_name
    
    exam_file = open(args.exam, 'rb')
    exam_pdf_reader = PyPDF2.PdfFileReader(exam_file)
    
    marks_file = open(args.marks, 'rb')
    marks_pdf_reader = PyPDF2.PdfFileReader(marks_file)
     
    os_utils.mkdir_if_nonexistent(args.output)   
    
    for idx in range(marks_pdf_reader.numPages): 
        out_writer = PyPDF2.PdfFileWriter()
        mark_page = marks_pdf_reader.getPage(idx)
        for exam_page_number in range(exam_pdf_reader.numPages):
            exam_page_original = exam_pdf_reader.getPage(exam_page_number)
            exam_page = copy.copy(exam_page_original)
            exam_page.mergePage(mark_page)
            out_writer.addPage(exam_page)
        out_file_name = '{0}_{1:03d}.pdf'.format(exam_name, idx)
        out_file = open(os.path.join(args.output, out_file_name), 'wb')
        out_writer.write(out_file)
        out_file.close()
        
    exam_file.close()
    marks_file.close()