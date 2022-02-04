const supertest = require('supertest');

describe('API Tests', () => {
  let server;
  let request;
  before(() => {
    const api = require('../index');
    server = api.server;
    request = supertest(api.app);
  });

  after(() => {
    server.close();
  });

  it('The api works!', async () => {
    await request.get('/')
      .expect(200);
  });
});