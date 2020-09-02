# Hubdoc Document Intake

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
any languages or frameworks you are comfortable with. Please include any notes
on the platform (OS) used and if a non-Node service is provided, please include
setup notes.

## We expect the following from you:

* Working code that accomplishes the task outlined above.
* Corresponding tests (unit and integration tests are both acceptable).

## We do NOT expect you to worry about the following:

* User authentication or any other form of endpoint security
  * *For senior candidates we may ask how you would accomplish this, but we
    don't expect to see code here*
* Virus checking or document format validation (i.e. you can assume we will
  send you valid pdfs)
