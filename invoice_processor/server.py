import uvicorn, json, sqlite3
from threading import Thread, Lock
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
dbMutex = Lock()

class ProcessingJob(Base):
    __tablename__ = "ProcessingJob"
    uuid = Column(Text, primary_key=True, nullable=False)
    uploadedBy = Column(Text, nullable=False)
    uploadTimestamp = Column(REAL, nullable=False)
    filesize = Column(Integer, nullable=False)
    vendorName = Column(Text)
    invoiceDate = Column(Text)
    total = Column(REAL)
    paid = Column (REAL)
    totalDue = Column(REAL)
    currency = Column(Text)
    taxAmount = Column(REAL)
    processingStatus = Column(Text, nullable=False)
    pdf = Column(BLOB, nullable=False)

Base.metadata.create_all(engine)

Session = sessionmaker(bind=engine)
session = Session()

def insertPendingJob(uploadedBy, pdf):
    uuid = uuid4().hex
    filesize = len(pdf)
    uploadTimestamp = time()

    job = ProcessingJob(uuid=uuid, uploadedBy=uploadedBy, uploadTimestamp=uploadTimestamp,
        processingStatus='PENDING', filesize=filesize, pdf=pdf)
    session.add(job)
    session.commit()
    return uuid

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
