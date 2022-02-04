import stanza
from io import StringIO, BytesIO
from pdfminer.pdfparser import PDFParser
from pdfminer.converter import TextConverter
from pdfminer.pdfdevice import TagExtractor
from pdfminer.pdfinterp import PDFResourceManager, PDFPageInterpreter
from pdfminer.pdfdocument import PDFDocument
from pdfminer.layout import LAParams
from pdfminer.pdfpage import PDFPage

class TextFragment(object):
    def __init__(self, textFragment):
        self.text = self.textFragment

def main():
    with open("../invoices/HubdocInvoice1.pdf", "rb") as inputFile:
        minedText1 = mineText1(inputFile)
        minedText2 = mineText2(inputFile)

    fragments = [textFragment for textFragment in 
            filter(
                lambda s: len(s) > 0,
                (map(
                    lambda s: s.strip(), 
                    minedText1.split('\n'))
                )
            )
        ]

    # print(fragments)
    # print('\n\n\n\n')
    # print(minedText2)
    # print('\n\n\n\n')

    for fr in fragments:
        positions = list(findall(fr, minedText2))
        print(fr, positions)

    # nlp = stanza.Pipeline(lang='en', processors='tokenize,ner', verbose=False)
    # for frag in fragments:
    #     doc = nlp(frag)
    #     print(frag, repr(doc.ents))
    #     print()

def findall(p, s): # from https://stackoverflow.com/a/34445090
    '''Yields all the positions of
    the string p in the string s.'''
    i = s.find(p)
    while i != -1:
        yield i
        i = s.find(p, i+1)

def mineText1(inputFile):
    outputString = StringIO()
    pdfParser = PDFParser(inputFile)
    pdfDocument = PDFDocument(pdfParser)
    rsrcmgr = PDFResourceManager()
    device = TextConverter(rsrcmgr, outputString, laparams=LAParams())
    interpreter = PDFPageInterpreter(rsrcmgr, device)
    for page in PDFPage.create_pages(pdfDocument):
        interpreter.process_page(page)
    return outputString.getvalue()

def mineText2(inputFile):
    outputFile = BytesIO()
    resourceManager = PDFResourceManager()
    device = TagExtractor(resourceManager, outputFile, codec='utf-8')
    interpreter = PDFPageInterpreter(resourceManager, device)
    for page in PDFPage.get_pages(inputFile):
        interpreter.process_page(page)
    return outputFile.getvalue().decode()

if __name__ == '__main__':
    main()

