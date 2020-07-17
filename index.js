const express = require('express');
const multer  = require('multer');
const app = express();
const port = 3000;

const upload = multer();

app.get('/', (req, res) => res.send('Hello Hubdoc!'));

app.post('/upload', upload.single('file'), (req, res, next) => {

  // req.file is the uploaded file
  // req.body will hold the text fields, if there were any
  // e.g. req.body.email should have the email address

  res.sendStatus(200);
})

const server = app.listen(port, () => console.log(`Hubdoc Intake listening on port ${port}!`))

module.exports = {
  app,
  server
};
