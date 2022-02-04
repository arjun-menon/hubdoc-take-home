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
        self.text = textFragment
        self.pos = None
        self.entities = None
    def __str__(self):
        return '%s %r' % (self.text, self.entities)

def main():
    fragments = constructFragments('../invoices/HubdocInvoice1.pdf')

    for fr in fragments:
        print(fr, '\n')

def constructFragments(filename):
    with open(filename, 'rb') as inputFile:
        minedTextNormal = mineText1(inputFile)
        minedTextTagged = mineText2(inputFile)

    fragments = [TextFragment(textFragment) for textFragment in 
            filter(
                lambda s: len(s) > 0,
                (map(
                    lambda s: s.strip(), 
                    minedTextNormal.split('\n'))
                )
            )
        ]

    for fr in fragments:
        fr.pos = list(findall(fr.text, minedTextTagged))

    seen = set()
    for fr in fragments:
        assert isinstance(fr.pos, list)
        assert len(fr.pos) > 0

        if len(fr.pos) == 1:
            fr.pos = fr.pos[0]
            seen.add(fr.pos)
        elif len(fr.pos) > 1:
            for a_pos in fr.pos:
                (start, end) = a_pos
                if not isInRanges(start, seen) and not isInRanges(end, seen):
                    fr.pos = a_pos
                    seen.add(fr.pos)
                    break

    for fr in fragments:
        assert isinstance(fr.pos, tuple)
        start, _ = fr.pos
        fr.pos = start
        assert isinstance(fr.pos, int)

    fragments.sort(key=lambda fr: fr.pos)

    nlp = stanza.Pipeline(lang='en', processors='tokenize,ner', verbose=False)
    for fr in fragments:
        doc = nlp(fr.text)
        fr.entities = doc.ents

    return fragments

def isInRanges(n, ranges):
        for (start, end) in ranges:
            if n >= start and n <= end:
                return True
        return False

def findall(p, s): # based on https://stackoverflow.com/a/34445090
    '''Yields all the positions of
    the string p in the string s.'''
    i = s.find(p)
    while i != -1:
        yield (i, i + len(p) - 1)
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

