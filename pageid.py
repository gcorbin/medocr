class PageId:
    def __init__(self, data=None):
        self.exam = None
        self.task = None
        self.page = None
        if data is not None:
            if isinstance(data, str):
                self.init_from_ocr_string(data)
            elif isinstance(data, tuple) or isinstance(data, list):
                if len(data) != 3:
                    raise ValueError('A PageId object needs 3 values to be constructed.')
                self.exam = data[0]
                self.task = data[1]
                self.page = data[2]
            else:
                raise TypeError('A PageId needs a tuple or a string to be constructed.')

    def tuple(self):
        return self.exam, self.task, self.page

    def is_valid(self):
        return self.exam is not None \
               and self.task is not None\
               and self.page is not None

    def __str__(self):
        return 'Klausur {}, Aufgabe {}, Seite {}'.format(self.exam, self.task, self.page)

    @staticmethod
    def tokenize_ocr_string(data):
        ocr_string = ''.join(data.split()).upper()
        return ocr_string.split('/')

    def init_from_ocr_string(self, data):
        ocr_tokens = PageId.tokenize_ocr_string(data)

        for token in ocr_tokens:
            if token.startswith('KLAUSUR'):
                subtokens = token.split('KLAUSUR')
                number = subtokens[1]
                if number.isdigit():
                    self.exam = int(number)
            elif token.startswith('AUFGABE'):
                subtokens = token.split('AUFGABE')
                number = subtokens[1]
                if number.isdigit():
                    self.task = int(number)
            elif token.startswith('DECKBLATT'):
                self.task = 0
            elif token.startswith('SEITE'):
                subtokens = token.split('SEITE')
                self.page = subtokens[1]
            elif token.startswith('EXTRASEITE'):
                self.page = 0
            elif token == '':
                pass
            else:
                pass