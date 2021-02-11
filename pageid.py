def compute_checksum(number):
    if number < 0 or number > 999:
        raise ValueError('Checksums are only defined for three-digit positive integers, got {}'.format(number))
    # last digit of the sum of digits
    checksum = (number // 100) + (number % 100) // 10 + (number % 10)
    return checksum % 10


def split_checksum(number):
    number = number // 10
    checksum = number % 10
    return number, checksum


def get_number_from_ocr_string(ocr_string):
    ocr_string = ''.join(ocr_string.split())  # remove all whitespace
    try:
        ocr_int = int(ocr_string)
    except ValueError as e:
        return None
    number, checksum = split_checksum(ocr_int)
    if checksum != compute_checksum(number):
        return None

    return number


def page_id_from_ocr(exam_id, ocr_strings):
    if len(ocr_strings) != 3:
        return PageId()
    pid = PageId()
    pid.exam = exam_id
    pid.sheet = get_number_from_ocr_string(ocr_strings[0])
    if ocr_strings[1] != '':
        pid.task = get_number_from_ocr_string(ocr_strings[1])
    else:
        pid.task = -1

    pid.page = get_number_from_ocr_string(ocr_strings[2])
    return pid


class PageId:
    def __init__(self, data=None):
        self.exam = None
        self.sheet = None
        self.task = None
        self.page = None
        if data is not None:
            self.exam = data[0]
            self.sheet = data[1]
            self.task = data[2]
            self.page = data[3]

    def tuple(self):
        return self.exam, self.sheet, self.task, self.page

    def is_valid(self):
        return self.exam is not None \
               and self.sheet is not None\
               and self.task is not None\
               and self.page is not None

    def is_empty_page(self):
        return self.is_valid() and self.task < 0

    def __str__(self):
        return 'Klausur {}, Bogen {}, Aufgabe {}, Seite {}'.format(self.exam, self.sheet, self.task, self.page)



