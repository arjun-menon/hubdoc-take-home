import queue, uvicorn
# from threading import Thread
from uuid import uuid4
from time import time
from io import BytesIO
from starlette.applications import Starlette
from starlette.responses import JSONResponse, PlainTextResponse
from sqlalchemy import Column, Integer, Text, BLOB, REAL, create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, scoped_session
from sqlalchemy.pool import SingletonThreadPool
from processor import constructFragmentedDocFromFile, KeyInformation

verbose_level = 1  # This can be 0, 1, or 2

engine = create_engine('sqlite://', poolclass=SingletonThreadPool,
    connect_args={'check_same_thread': False}, echo=verbose_level >= 2)
Base = declarative_base()

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

sessionMake = sessionmaker(bind=engine)
Session = scoped_session(sessionMake)
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

def updateRowWithInfo(row, info):
    row.vendorName = info.vendorName
    row.invoiceDate = info.invoiceDate
    row.total = info.total
    row.paid = info.paid
    row.totalDue = info.totalDue
    row.currency = info.currency
    row.taxAmount = info.taxAmount
    row.processingStatus = 'DONE'

q = queue.Queue()

async def doWork():
    while not q.empty(): # True:
        id = q.get_nowait() # q.get(block=True, timeout=None)
        if id:
            # print(f'Working on {id}')
            row = session.query(ProcessingJob).get(id)
            pdf = row.pdf

            if isinstance(pdf, bytes):
                pdfBytesFiles = BytesIO(pdf)
                fd = constructFragmentedDocFromFile(pdfBytesFiles)
                info = KeyInformation.extractFromFragmentedDoc(fd)
                updateRowWithInfo(row, info)
                session.commit()

            # print(f'Finished {id}')
            q.task_done()

# Thread(target=worker, daemon=True).start()

app = Starlette(debug=True)

@app.route('/upload', methods=['POST'])
async def upload(request):
    form = await request.form()
    email = form["email"]
    file = form["file"].file
    fileBytes = file.read()
    id = insertPendingJob(email, fileBytes)
    q.put(id)
    await doWork() # need to parallelize
    return JSONResponse({'id': id})

@app.route('/document/{id:str}', methods=['GET'])
async def document(request):
    id = request.path_params['id']
    Session = scoped_session(sessionmaker(bind=engine))
    row = Session.query(ProcessingJob).get(id)
    if row:
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
    else:
        return PlainTextResponse('Not found.', status_code=404)

uvicorn.run(app, host='localhost', port=3000, log_level='info' if verbose_level >= 1 else 'error')
