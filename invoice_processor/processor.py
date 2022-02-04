import stanza
from io import StringIO, BytesIO
from pdfminer.pdfparser import PDFParser
from pdfminer.converter import TextConverter
from pdfminer.pdfdevice import TagExtractor
from pdfminer.pdfinterp import PDFResourceManager, PDFPageInterpreter
from pdfminer.pdfdocument import PDFDocument
from pdfminer.layout import LAParams
from pdfminer.pdfpage import PDFPage

def main():
    print('Processing...\n')

    with open("../invoices/HubdocInvoice1.pdf", "rb") as inputFile:
        minedText1 = mineText1(inputFile)
        minedText2 = mineText2(inputFile)

    print(minedText1)
    print('\n\n\n\n')
    print(minedText2)
    print('\n\n\n\n')

    nlp = stanza.Pipeline(lang='en', processors='tokenize,ner')
    doc = nlp(minedText1)
    print(*[f'entity: {ent.text}\ttype: {ent.type}\tstr: \
{minedText1[ent.start_char:ent.end_char]}' for ent in doc.ents], sep='\n')

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

