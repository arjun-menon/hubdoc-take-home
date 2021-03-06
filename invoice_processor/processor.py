import stanza, os, pickle
from hashlib import blake2b
from io import StringIO, BytesIO
from pdfminer.pdfparser import PDFParser
from pdfminer.converter import TextConverter
from pdfminer.pdfdevice import TagExtractor
from pdfminer.pdfinterp import PDFResourceManager, PDFPageInterpreter
from pdfminer.pdfdocument import PDFDocument
from pdfminer.layout import LAParams
from pdfminer.pdfpage import PDFPage

#
# Usage:
#   call the function extractKeyInformation(filename)
#   with the path to the file to be processed.
#
# Example:
#   > from processor import extractKeyInformation
#   > keyInfo = extractKeyInformation('../invoices/HubdocInvoice1.pdf')
#
# Example output:
#   > keyInfo
#   > {'vendorName': 'Hubdoc', 'invoiceDate': 'February 22, 2019', 'currency': 'GBP', 'taxAmount': 0.0, 'total': 22.5, 'totalDue': 0.0, 'paid': -22.5}
#
#

currency_codes = {'CAD', 'USD', 'GBP', 'AUD', 'NZD'}

class TextFragment(object):
    def __init__(self, textFragment):
        self.text = textFragment
        self.pos = None
        self.entities = []

    def entityTypes(self):
        return [ent.type for ent in self.entities]

    def __str__(self):
        return '%s --> %r' % (self.text, self.entityTypes())

class FragmentedDoc(object):
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

    def findCurrencyCodes(self):
        currencies = []
        for fr in self.fragments:
            if fr.text in currency_codes:
                currencies.append(fr.text)
        return currencies

    def findPercentsWithIndices(self):
        return self.getAllEntitiesOfType('PERCENT', True)

    def findFragmentByIncasesensitiveText(self, searchText):
        searchText = searchText.strip().casefold()
        for index, fr in enumerate(self.fragments):
            if fr.text.casefold() == searchText:
                return index
        return None

def getVendorName(f):
    orgs = f.getOrgs()

    # in all of the example invoices, the last organization was the vendor
    vendorName = orgs[-1]

    return vendorName

def getInvoiceDate(f):
    dates = f.getDates()

    # in all of the example invoices, the first date was the invoice date
    invoiceDate = dates[0]

    return invoiceDate

def getCurrency(f):
    currencies = f.findCurrencyCodes()

    # we only expect there to be one currency code in the PDF, based on example invoices
    # in a proper implementation, we do something different here (throw an exception, or attempt to narrow down to the right currency).
    assert len(currencies) == 1
    currency = currencies[0]

    return currency

def extractAmountFromMoneyFragment(moneyFragment):
    # the assertions below are based on structural expectations based on the example invoices
    # in a proper implementation, we'd replace these assertions with intelligent hueristics, guesses, and/or with exceptions thrown.
    assert len(moneyFragment.entities) == 1
    moneyEntity = moneyFragment.entities[0]
    assert moneyEntity.type == 'MONEY'
    moneyAmount = round(float(moneyEntity.text), 2)

    # if the amount is negative, we make the stanza entity amount negative as well
    if moneyFragment.text[0] == '-':
        moneyAmount *= -1

    return moneyAmount

def getTaxAmount(f):
    percents = f.findPercentsWithIndices()

    # we grab the last percent as the tax, based on the example invoices
    _, lastPercentIndex = percents[-1]
    taxFragment = f.fragments[lastPercentIndex + 1]
    taxAmount = extractAmountFromMoneyFragment(taxFragment)

    return taxAmount

def getTotal(f):
    totalTextFragmentIndex = f.findFragmentByIncasesensitiveText('total')
    # we grab the money amount that appears right after 'Total'
    totalFragment = f.fragments[totalTextFragmentIndex + 1]
    total = extractAmountFromMoneyFragment(totalFragment)

    return total

def getTotalDue(f):
    totalDueTextFragmentIndex = f.findFragmentByIncasesensitiveText('total due')
    # we grab the money amount that appears right after 'Total Due'
    totalDueFragment = f.fragments[totalDueTextFragmentIndex + 1]
    totalDue = extractAmountFromMoneyFragment(totalDueFragment)

    return totalDue

def getPaidAmount(f):
    paidTextFragmentIndex = f.findFragmentByIncasesensitiveText('paid')
    # we grab the money amount that appears right after 'Paid'
    paidAmountFragment = f.fragments[paidTextFragmentIndex + 1]
    paid = extractAmountFromMoneyFragment(paidAmountFragment)

    return paid

class KeyInformation(object):
    def __init__(self, keyInfo):
        self.keyInfo = keyInfo
        self.__dict__.update(self.keyInfo)

    @classmethod
    def extractFromFragmentedDoc(classKeyInformation, f):
        vendorName = getVendorName(f)
        invoiceDate = getInvoiceDate(f)
        currency = getCurrency(f)
        taxAmount = getTaxAmount(f)
        total = getTotal(f)
        totalDue = getTotalDue(f)
        paid = getPaidAmount(f)

        return classKeyInformation({
            'vendorName': vendorName,
            'invoiceDate': invoiceDate,
            'currency': currency,
            'taxAmount': taxAmount,
            'total': total,
            'totalDue': totalDue,
            'paid': paid
        })

    def print(self):
        print('vendorName:', self.vendorName)
        print('invoiceDate:', self.invoiceDate)
        print('currency:', self.currency)
        print('taxAmount:', self.taxAmount)
        print('total:', self.total)
        print('paid:', self.paid)
        print('totalDue:', self.totalDue)

def extractKeyInformation(filename):
    f = constructFragmentedDoc(filename)
    keyInfoObject = KeyInformation.extractFromFragmentedDoc(f)
    return keyInfoObject.keyInfo

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
        f = constructFragmentedDoc(filename)
        with open(pick_filepath, 'wb') as pickle_file:
            pickle.dump(f, pickle_file)
    else:
        with open(pick_filepath, 'rb') as pickle_file:
            f = pickle.load(pickle_file)

    return f

def testKeyInformationExtraction(f):
    print('--------------------------------------------------------------------------------------------------------------')
    keyInfo = KeyInformation.extractFromFragmentedDoc(f)
    keyInfo.print()

def testRun():
    f1 = pickledLoad('../invoices/HubdocInvoice1.pdf')
    f2 = pickledLoad('../invoices/HubdocInvoice2.pdf')
    f3 = pickledLoad('../invoices/HubdocInvoice3.pdf')
    f4 = pickledLoad('../invoices/HubdocInvoice4.pdf')
    f5 = pickledLoad('../invoices/HubdocInvoice5.pdf')

    testKeyInformationExtraction(f1)
    testKeyInformationExtraction(f2)
    testKeyInformationExtraction(f3)
    testKeyInformationExtraction(f4)
    testKeyInformationExtraction(f5)

def main():
    print('Running tests against example invoices...')
    testRun()

def constructFragmentedDoc(filename):
    with open(filename, 'rb') as inputFile:
        constructFragmentedDocFromFile(inputFile)

def constructFragmentedDocFromFile(inputFile):
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

    return FragmentedDoc(fragments)

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

