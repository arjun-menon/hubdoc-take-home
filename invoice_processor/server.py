import uvicorn, json, sqlite3
from uuid import uuid4
from time import time
from processor import extractKeyInformation
from starlette.applications import Starlette
from starlette.responses import JSONResponse

class ProcessingJobs(object):
    def __init__(self):
        self.sqlConn = sqlite3.connect(':memory:')
        self.dbCur = self.sqlConn.cursor()

        self.dbCur.execute(
            '''CREATE TABLE ProcessingJob(
                    uuid TEXT PRIMARY KEY NOT NULL,
                    uploadedBy TEXT NOT NULL,
                    uploadTimestamp REAL NOT NULL,
                    filesize INTEGER,
                    vendorName TEXT,
                    invoiceDate TEXT,
                    total REAL,
                    totalDue REAL,
                    currency TEXT,
                    taxAmount REAL,
                    processingStatus TEXT,
                    pdf BLOB NOT NULL)''')

    def insertJobRow(self, uuid, uploadedBy, uploadTimestamp, filesize, vendorName, invoiceDate, total, totalDue, currency, taxAmount, processingStatus, pdf):
        self.dbCur.execute('''INSERT INTO ProcessingJob(
            uuid, uploadedBy, uploadTimestamp, filesize, vendorName, invoiceDate, total, totalDue, currency, taxAmount, processingStatus, pdf)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)''',
            (uuid, uploadedBy, uploadTimestamp, filesize, vendorName, invoiceDate, total, totalDue, currency, taxAmount, processingStatus, pdf))

    def insertPendingJob(self, uploadedBy, pdf):
        uuid = uuid4().hex
        filesize = len(pdf)
        uploadTimestamp = time()
        self.dbCur.execute('''INSERT INTO ProcessingJob(
            uuid, uploadedBy, uploadTimestamp, filesize, processingStatus, pdf)
            VALUES (?, ?, ?, ?, ?, ?)''', (uuid, uploadedBy, uploadTimestamp, filesize, 'PENDING', pdf))
        return uuid

    def print(self):
        for row in self.dbCur.execute('SELECT * FROM ProcessingJob'):
            print(row)

jobs = ProcessingJobs()

app = Starlette(debug=True)

@app.route('/upload', methods=['POST'])
async def upload(request):
    form = await request.form()
    email = form["email"]
    file = form["file"].file
    fileBytes = file.read()
    uuid = jobs.insertPendingJob(email, fileBytes)
    return JSONResponse({'id': uuid})

@app.route('/document', methods=['GET'])
async def document(request):
    return JSONResponse({'id': 'todo'})

uvicorn.run(app, host='localhost', port=3000, log_level='info')
