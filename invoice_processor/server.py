import uvicorn, json, sqlite3
from uuid import uuid4
from time import time
from processor import extractKeyInformation
from starlette.applications import Starlette
from starlette.responses import JSONResponse
from sqlalchemy import Column, Integer, Text, BLOB, REAL, create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship, backref, sessionmaker, joinedload

verbose = True

engine = create_engine('sqlite://', echo=verbose)

Base = declarative_base()

class ProcessingJob(Base):
    __tablename__ = "ProcessingJob"
    uuid = Column(Text, primary_key=True, nullable=False)
    uploadedBy = Column(Text, nullable=False)
    uploadTimestamp = Column(REAL, nullable=False)
    filesize = Column(Integer)
    vendorName = Column(Text)
    invoiceDate = Column(Text)
    total = Column(REAL)
    totalDue = Column(REAL)
    currency = Column(Text)
    taxAmount = Column(REAL)
    processingStatus = Column(Text, nullable=False)
    pdf = Column(BLOB)

Base.metadata.create_all(engine)

Session = sessionmaker(bind=engine)
session = Session()

def insertPendingJob(uploadedBy, pdf):
    uuid = uuid4().hex
    filesize = len(pdf)
    uploadTimestamp = time()

    # self.dbCur.execute('''INSERT INTO ProcessingJob(
    #     uuid, uploadedBy, uploadTimestamp, filesize, processingStatus, pdf)
    #     VALUES (?, ?, ?, ?, ?, ?)''', (uuid, uploadedBy, uploadTimestamp, filesize, 'PENDING', pdf))

    job = ProcessingJob(uuid=uuid, uploadedBy=uploadedBy, uploadTimestamp=uploadTimestamp,
        processingStatus='PENDING', pdf=pdf)

    session.add(job)
    session.commit()

    return uuid

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
    uuid = insertPendingJob(email, fileBytes)
    return JSONResponse({'id': uuid})

@app.route('/document/{id:str}', methods=['GET'])
async def document(request):
    id = request.path_params['id']
    print('Seeking ID:', id)
    for row in session.query(ProcessingJob).filter(ProcessingJob.uuid == id):
        return JSONResponse({
            'uploadedBy': row.uploadedBy,
            'uploadTimestamp': row.uploadTimestamp,
            'filesize': row.filesize,
            'vendorName': row.vendorName,
            'invoiceDate': row.invoiceDate,
            'total': row.total,
            'totalDue': row.totalDue,
            'currency': row.currency,
            'taxAmount': row.taxAmount,
            'processingStatus': row.processingStatus,
        })

uvicorn.run(app, host='localhost', port=3000, log_level='info' if verbose else 'error')
