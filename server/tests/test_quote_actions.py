import unittest
from uuid import UUID, uuid4

from app.quotes.models import QuoteStatus
from tests import test_quote_patch


class QuoteActionTests(unittest.TestCase):
    setUpClass = classmethod(test_quote_patch.QuotePatchTests.setUpClass.__func__)
    setUp = test_quote_patch.QuotePatchTests.setUp
    drop_test_schema = test_quote_patch.QuotePatchTests.drop_test_schema
    login = test_quote_patch.QuotePatchTests.login
    payload = test_quote_patch.QuotePatchTests.payload
    post = test_quote_patch.QuotePatchTests.post
    get = test_quote_patch.QuotePatchTests.get

    def action(self, action, url=None, **kwargs):
        return self.client.post((url or self.url) + '/' + action,
                                headers={'Authorization': 'Bearer ' + self.token}, **kwargs)

    def assert_action_success(self, action, target):
        before = self.get()
        response = self.action(action)
        self.assertEqual(response.status_code, 200, response.text)
        self.assertEqual(response.headers['cache-control'], 'no-store')
        self.assertEqual(set(response.json()), {'data'})
        saved = response.json()['data']
        self.assertEqual(saved['status'], target)
        self.assertEqual(saved, self.get())
        self.assertGreater(saved['updated_at'], before['updated_at'])
        for field in before.keys() - {'status', 'updated_at'}:
            self.assertEqual(saved[field], before[field], field)
        self.assertTrue(all(connection.closed for connection in self.request_connections))

    def assert_action_rejects_statuses(self, action, allowed):
        for status in QuoteStatus:
            if status in allowed:
                continue
            self.connection.execute('UPDATE quotes SET status = %s WHERE id = %s',
                                    (status.value, UUID(self.quote['id'])))
            before = self.get()
            with self.subTest(action=action, status=status):
                response = self.action(action)
                self.assertEqual(response.status_code, 409)
                self.assertEqual(response.json()['error']['code'], 'INVALID_QUOTE_STATUS')
                self.assertEqual(self.get(), before)

    def assert_action_access_and_contract(self, action):
        for headers in ({}, {'Authorization': 'Bearer invalid'}):
            self.assertEqual(self.client.post(self.url + '/' + action, headers=headers).status_code, 401)
        self.assertEqual(self.action(action, '/api/v1/quotes/bad').status_code, 422)
        self.client.post('/api/v1/auth/register', json={
            'name': 'Other', 'email': 'other@example.com', 'password': 'ExactPassword123',
        })
        owner_token = self.token
        self.token = self.login(email='other@example.com').json()['data']['access_token']
        foreign = self.action(action)
        missing = self.action(action, '/api/v1/quotes/' + str(uuid4()))
        self.assertEqual(foreign.status_code, 404)
        self.assertEqual(foreign.json(), missing.json())
        self.assertEqual(foreign.json()['error']['code'], 'QUOTE_NOT_FOUND')
        self.token = owner_token
        self.assertEqual(self.get(), self.quote)
        operation = self.client.get('/openapi.json').json()['paths'][
            '/api/v1/quotes/{quote_id}/' + action]['post']
        self.assertEqual(operation['security'], [{'HTTPBearer': []}])
        self.assertIn('200', operation['responses'])
        self.assertNotIn('requestBody', operation)

    def test_send_returns_persisted_sent_quote(self):
        self.assert_action_success('send', 'SENT')

    def test_send_rejects_every_non_draft_status(self):
        self.assert_action_rejects_statuses('send', {QuoteStatus.DRAFT})

    def test_send_access_and_contract(self):
        self.assert_action_access_and_contract('send')

    def test_accept_returns_persisted_accepted_quote_from_draft_and_sent(self):
        for status in ('DRAFT', 'SENT'):
            self.connection.execute('UPDATE quotes SET status = %s WHERE id = %s',
                                    (status, UUID(self.quote['id'])))
            with self.subTest(status=status):
                self.assert_action_success('accept', 'ACCEPTED')

    def test_accept_rejects_every_other_status(self):
        self.assert_action_rejects_statuses('accept', {QuoteStatus.DRAFT, QuoteStatus.SENT})

    def test_accept_access_and_contract(self):
        self.assert_action_access_and_contract('accept')
