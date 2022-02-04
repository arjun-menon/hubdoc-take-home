import stanza
from io import StringIO, BytesIO
from pdfminer.pdfparser import PDFParser
from pdfminer.converter import TextConverter
from pdfminer.pdfdevice import TagExtractor
from pdfminer.pdfinterp import PDFResourceManager, PDFPageInterpreter
from pdfminer.pdfdocument import PDFDocument
from pdfminer.layout import LAParams
from pdfminer.pdfpage import PDFPage

class Entity(object):
    pass

def main():
    print('Processing...\n')

    with open("../invoices/HubdocInvoice1.pdf", "rb") as inputFile:
        minedText1 = mineText1(inputFile)
        minedText2 = mineText2(inputFile)

    fragments = list(filter(lambda s: len(s) > 0, (map(lambda s: s.strip(), minedText1.split('\n')))))

    print(fragments)
    print('\n\n\n\n')
    print(minedText2)
    print('\n\n\n\n')

    nlp = stanza.Pipeline(lang='en', processors='tokenize,ner', verbose=False)
    for frag in fragments:
        doc = nlp(frag)
        print(frag, repr(doc.ents))
        print()

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
    resourceManager = PDFResourceManager(caching=False)
    device = TagExtractor(resourceManager, outputFile, codec='utf-8')
    interpreter = PDFPageInterpreter(resourceManager, device)
    for page in PDFPage.get_pages(inputFile, caching=False):
        interpreter.process_page(page)
    return outputFile.getvalue().decode()

if __name__ == '__main__':
    main()

