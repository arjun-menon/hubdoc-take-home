from email.policy import default
import stanza, os, pickle
from hashlib import blake2b
from io import StringIO, BytesIO
import dateutil.parser as dateParser
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
        self.entities = []

    def entityTypes(self):
        return [ent.type for ent in self.entities]

    def __str__(self):
        return '%s --> %r' % (self.text, self.entityTypes())

class FileToProcess(object):
    def __init__(self, fragments):
        self.fragments = fragments

    def print(self):
        for fr in self.fragments:
            print(fr)

    def getAllEntitiesOfType(self, entityType, withLocation=False):
        entityTexts = []
        for index, fr in enumerate(self.fragments):
            for ent in fr.entities:
                if ent.type == entityType:
                    if withLocation:
                        entityTexts.append((ent.text, index))
                    else:
                        entityTexts.append(ent.text)
        return entityTexts

    def getOrgs(self):
        orgs = self.getAllEntitiesOfType('ORG')
        return orgs

    def getDates(self):
        dateStrs = self.getAllEntitiesOfType('DATE')
        # dates = [(dateStr + '-->' + repr(dateParser.parse(dateStr, default=None))) for dateStr in dateStrs]
        # print('Dates: %r' % dateStrs)
        return dateStrs

def extractKeyInformation(f):
    f.print()
    orgs = f.getOrgs()
    dates = f.getDates()

    # in all of the example invoices, the last organization was the vendor
    vendorName = orgs[-1]

    # in all of the example invoices, the first date was the invoice date
    invoiceDate = dates[0]

    print('vendorName:', vendorName)
    print('invoiceDate:', invoiceDate)

    print('--------------------------------------------------------------------------------------------------------------')

hash = blake2b(digest_size=5)

def pickledLoad(filename):
    filename_root, filename_ext = os.path.splitext(filename)
    hash.update(filename_root.encode())
    filename_root_hash = hash.hexdigest()
    filename_path = os.path.split(filename_root)
    assert filename_ext == '.pdf'
    pickle_filename = filename_path[-1] + '-' + filename_root_hash + '.pickle'
    pick_filepath = os.path.join('storage/', pickle_filename)

    if not os.path.isfile(pick_filepath):
        f = FileToProcess(constructFragments(filename))
        with open(pick_filepath, 'wb') as pickle_file:
            pickle.dump(f, pickle_file)
    else:
        with open(pick_filepath, 'rb') as pickle_file:
            f = pickle.load(pickle_file)

    return f

def main():
    f1 = pickledLoad('../invoices/HubdocInvoice1.pdf')
    f2 = pickledLoad('../invoices/HubdocInvoice2.pdf')
    f3 = pickledLoad('../invoices/HubdocInvoice3.pdf')
    f4 = pickledLoad('../invoices/HubdocInvoice4.pdf')
    f5 = pickledLoad('../invoices/HubdocInvoice5.pdf')

    extractKeyInformation(f1)
    extractKeyInformation(f2)
    extractKeyInformation(f3)
    extractKeyInformation(f4)
    extractKeyInformation(f5)

def constructFragments(filename):
    with open(filename, 'rb') as inputFile:
        minedTextNormal = mineTextNormal(inputFile)
        minedTextTagged = mineTextTagged(inputFile)

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

def mineTextNormal(inputFile):
    outputString = StringIO()
    pdfParser = PDFParser(inputFile)
    pdfDocument = PDFDocument(pdfParser)
    rsrcmgr = PDFResourceManager()
    device = TextConverter(rsrcmgr, outputString, laparams=LAParams())
    interpreter = PDFPageInterpreter(rsrcmgr, device)
    for page in PDFPage.create_pages(pdfDocument):
        interpreter.process_page(page)
    return outputString.getvalue()

def mineTextTagged(inputFile):
    outputFile = BytesIO()
    resourceManager = PDFResourceManager()
    device = TagExtractor(resourceManager, outputFile, codec='utf-8')
    interpreter = PDFPageInterpreter(resourceManager, device)
    for page in PDFPage.get_pages(inputFile):
        interpreter.process_page(page)
    return outputFile.getvalue().decode()

if __name__ == '__main__':
    main()

