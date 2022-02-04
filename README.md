# Solution Implementation Overview

### Overview

I've implemented the solution to this in Python.
My code lives inside `invoice_processor`.

There are two modules under `invoice_processor`: `server` and `processor`.

All of the logic for the PDF processing lives inside `processor`. The `processor` can be launched and tested separately.

### Using `processor` independently

If you import the function extractKeyInformation(filename) from processor, and give it a path to a file to be processed, you'll get back a dictionary with key fields extracted.

For example, on a Python prompt (while pwd is invoice_processor) we can:

    >>> from processor import extractKeyInformation
    >>> keyInfo = extractKeyInformation('../invoices/HubdocInvoice1.pdf')
    >>> keyInfo
    {'vendorName': 'Hubdoc', 'invoiceDate': 'February 22, 2019', 'currency': 'GBP', 'taxAmount': 0.0, 'total': 22.5, 'paid': -22.5, 'totalDue': 0.0}

If `processor.py` is run directly from the command-line, a set of tests (I suppose what are effectively integration tests) involving the 5 sample hubdoc invoices is run. The command-line output should display information extracted from all 5 of them.

### The server

The `server` does things like handling requests, remembering requests, and working on them. The server has two thread.

The main thread asynchronously handles API requests, while a second worker thread works on completing PDF processing tasks (it receives its work via Python's [queue](https://docs.python.org/3/library/queue.html) class that's designed for multithreading).

I've used `starlette` which is layer on top of `uvicorn` as my web framework, along with SQLAlchemy as my ORM, to build the server.

### Running

This project requires Postgres (or some other SQL server) as well as the the Python dependencies that are listed under `requirements.txt`, which are:
* pdfminer
* stanza
* uvicorn
* starlette
* python-multipart
* sqlalchemy
* psycopg2

To launch the server, the `server.py` should be run with a special URI representing the database to connect to as the sole argument, like so:

    python .\server.py postgresql://postgres:password@localhost/pdfprocessing

Note that `password` above must be replaced with the actual password. The `postgres` before the password is the postgres username. The `pdfprocessing` at the end is the database name.

# Hubdoc Document Intake (Problem Description)

## Background:

Hubdoc's customers upload millions of financial documents (receipts,
statements, invoices, etc...) each month. Having the documents themselves is
useful, and being able to identify key pieces of information within those
documents is even more useful.

### Your task is to implement a service that does the following:

* Exposes an HTTP endpoint, `/upload`
  * e.g. `curl -F 'file=@"invoices/HubdocInvoice1.pdf"' -F
    'email=user@domain.com' localhost:3000/upload`
  * Accepts a .pdf document and a user email in the body of the request
  * Attempts to extract the following data from the document
    * *Vendor Name* (e.g. Starbucks, Home Depot, McDonalds)
    * *Invoice Date*
    * *Total* (a positive or negative number with at most 2 decimal
      places)
    * *Total Due* (a positive or negative number with at most 2 decimal
      places)
    * *Currency* (a three character currency code; e.g. CAD, GBP)
    * *Tax Amount* (a positive or negative value with at most 2 decimal places)
  * Responds with a JSON payload containing an assigned document id:
  ```javascript
  { 
    id: '<some unique id>'
  }
  ```
* Exposes an HTTP endpoint, `/document/:id` 
  * `curl -XGET http://localhost:3000/document/:id` 
  * Respond with the following payload: 
  ```javascript 
  { 
    uploadedBy : '<user email address>',
    uploadTimestamp : '<timestamp>',
    filesize: '<filesize>',
    vendorName: '<vendor name>',
    invoiceDate: '<invoice date>',
    total: '<total>',
    totalDue: '<total due>',
    currency: '<currency>',
    taxAmount: '<tax amount>',
    processingStatus: '<status>',
  }
  ```
    * If you are unable to successfully extract a given field, you can set the
      response value to `null` or `undefined`.
    * The only fields that must always have a value are `processingStatus`,
      `uploadedBy` and `uploadTimestamp`.
    * `processingStatus` should reflect the current state of document
      processing after submission. This is open to your interpretation.

We have provided some bootstrap code that can accept a file upload. This
template uses the following tech stack:

* Node 10 or greater
* Express 4.x
* Multer

Within this package, you will find an `invoices` folder that contains a set of
Hubdoc invoices. Your service should correctly extract the expected fields from
all supplied invoices. Expect only files in the format of the invoices in this
folder.

Your service should also successfully process invoices from multiple concurrent
users.

While you are free to use whatever stack you'd like, we recommend you use the
`pdftotext` tool from the [poppler](https://poppler.freedesktop.org/) project
to extract text from pdf documents.  If you do use `pdftotext` or another tool
installed outside of your required modules, please make sure to tell us the
version required.

If using `pdftotext`:
* Mac users can install with [Homebrew](https://brew.sh/): `brew install poppler`
* Debian or Ubuntu Linux users can install with apt: `apt-get install -y
  poppler-utils`
* Windows users can install via [Scoop](https://scoop.sh/): `scoop install
  poppler`

Although Hubdoc's codebase is primarily written in JS, you are not required to
use any of the above tools or any of the provided code. Feel free to work with
any languages or frameworks you are comfortable with. If a non-Node service is
provided, please include setup notes.

Please also include:
* Your OS (e.g. Windows 10, MacOS Big Sur, Ubuntu 20.04 LTS)
* Version of dev platform used (e.g. Node 16.3.0, OpenJDK 18, .NET 5.0)
* Versions of any other runtime dependencies required to run and evaluate your
  assignment

## We expect the following from you:

* Working code that accomplishes the task outlined above.
* Corresponding tests (unit and integration tests are both acceptable).

## We do NOT expect you to worry about the following:

* User authentication or any other form of endpoint security
  * *For senior candidates we may ask how you would accomplish this, but we
    don't expect to see code here*
* Virus checking or document format validation (i.e. you can assume we will
  send you valid pdfs)
