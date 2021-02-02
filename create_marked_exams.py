import os
import copy
import PyPDF2


if __name__ == '__main__':
    # TODO parse arguments
    
    exam_name = 'klausur_va.pdf'
    marks_name = 'makeids.pdf'
    out_folder = 'marked_exams'
    
    exam_file = open(exam_name, 'rb')
    exam_pdf_reader = PyPDF2.PdfFileReader(exam_file)
    
    marks_file = open(marks_name, 'rb')
    marks_pdf_reader = PyPDF2.PdfFileReader(marks_file)
    
    
    for idx in range(marks_pdf_reader.numPages): 
        out_writer = PyPDF2.PdfFileWriter()
        mark_page = marks_pdf_reader.getPage(idx)
        for exam_page_number in range(exam_pdf_reader.numPages):
            exam_page_original = exam_pdf_reader.getPage(exam_page_number)
            exam_page = copy.copy(exam_page_original)
            exam_page.mergePage(mark_page)
            out_writer.addPage(exam_page)
        out_file_name = 'klausur_va_{0:03d}.pdf'.format(idx)
        out_file = open(os.path.join(out_folder, out_file_name), 'wb')
        out_writer.write(out_file)
        out_file.close()
        
    exam_file.close()
    marks_file.close()