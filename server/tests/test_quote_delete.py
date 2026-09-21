import unittest
from concurrent.futures import ThreadPoolExecutor
from threading import Barrier, Event
from unittest.mock import patch
from uuid import UUID, uuid4

from psycopg import errors, sql

from app.common.database import connect_database
from app.common.errors import DomainError
from app.quotes.models import QuoteStatus
from app.quotes import queries
from app.quotes.service import delete_quote
from tests import test_quote_patch


class QuoteDeleteTests(unittest.TestCase):
    setUpClass = classmethod(test_quote_patch.QuotePatchTests.setUpClass.__func__)
    setUp = test_quote_patch.QuotePatchTests.setUp
    drop_test_schema = test_quote_patch.QuotePatchTests.drop_test_schema
    login = test_quote_patch.QuotePatchTests.login
    payload = test_quote_patch.QuotePatchTests.payload
    post = test_quote_patch.QuotePatchTests.post
    get = test_quote_patch.QuotePatchTests.get

    def delete(self, url=None):
        return self.client.delete(url or self.url, headers={'Authorization': 'Bearer ' + self.token})

    def test_draft_deletion_cascades_only_own_items_and_never_reuses_number(self):
        other = self.post(self.payload()).json()['data']
        response = self.delete()
        self.assertEqual(response.status_code, 204)
        self.assertEqual(response.content, b'')
        self.assertEqual(self.connection.execute('SELECT count(*) FROM quote_items WHERE quote_id = %s',
                                                (UUID(self.quote['id']),)).fetchone()[0], 0)
        saved = self.client.get('/api/v1/quotes/' + other['id'],
                                headers={'Authorization': 'Bearer ' + self.token}).json()['data']
        self.assertEqual(saved, other)
        self.assertEqual(self.delete().status_code, 404)
        self.assertEqual(self.post(self.payload()).json()['data']['quote_number'], 'QT-0003')
        self.assertTrue(all(connection.closed for connection in self.request_connections))

    def test_every_non_draft_status_is_protected(self):
        for status in QuoteStatus:
            if status == QuoteStatus.DRAFT:
                continue
            self.connection.execute('UPDATE quotes SET status = %s WHERE id = %s',
                                    (status.value, UUID(self.quote['id'])))
            before = self.get()
            with self.subTest(status=status):
                response = self.delete()
                self.assertEqual(response.status_code, 409)
                self.assertEqual(response.json()['error']['code'], 'INVALID_QUOTE_STATUS')
                self.assertEqual(self.get(), before)

    def test_invoice_link_blocks_even_draft_and_preserves_invoice(self):
        invoice_id = self.connection.execute(
            '''INSERT INTO invoices (user_id, client_id, source_quote_id, invoice_number,
               issue_date, currency, subtotal, total)
               VALUES (%s, %s, %s, 'INV-0001', '2026-09-15', 'KES', 100, 106) RETURNING id''',
            (UUID(self.user_id), UUID(self.client_id), UUID(self.quote['id'])),
        ).fetchone()[0]
        invoice = self.connection.execute('SELECT * FROM invoices WHERE id = %s', (invoice_id,)).fetchone()
        response = self.delete()
        self.assertEqual(response.status_code, 409)
        self.assertEqual(self.get(), self.quote)
        self.assertEqual(self.connection.execute('SELECT * FROM invoices WHERE id = %s', (invoice_id,)).fetchone(), invoice)

    def test_authentication_foreign_missing_and_invalid_uuid(self):
        self.assertEqual(self.client.delete(self.url).status_code, 401)
        self.assertEqual(self.delete('/api/v1/quotes/bad').status_code, 422)
        self.client.post('/api/v1/auth/register', json={
            'name': 'Other', 'email': 'other@example.com', 'password': 'ExactPassword123',
        })
        owner_token = self.token
        self.token = self.client.post('/api/v1/auth/login', json={
            'email': 'other@example.com', 'password': 'ExactPassword123',
        }).json()['data']['access_token']
        foreign = self.delete()
        missing = self.delete('/api/v1/quotes/' + str(uuid4()))
        self.assertEqual(foreign.status_code, 404)
        self.assertEqual(foreign.json(), missing.json())
        self.assertEqual(foreign.json()['error']['code'], 'QUOTE_NOT_FOUND')
        self.token = owner_token
        self.assertEqual(self.get(), self.quote)

    def test_failed_cascade_and_outer_rollback_restore_quote_and_items(self):
        self.connection.execute('''CREATE FUNCTION reject_item_delete() RETURNS TRIGGER LANGUAGE plpgsql AS $$
            BEGIN RAISE EXCEPTION 'Private deletion detail'; END; $$;
            CREATE TRIGGER reject_item_delete BEFORE DELETE ON quote_items
            FOR EACH ROW EXECUTE FUNCTION reject_item_delete();''')
        response = self.delete()
        self.assertEqual(response.status_code, 500)
        self.assertNotIn('Private deletion detail', response.text)
        self.assertEqual(self.get(), self.quote)
        self.connection.execute('DROP TRIGGER reject_item_delete ON quote_items')
        with self.assertRaisesRegex(RuntimeError, 'abort'):
            with self.connection.transaction():
                delete_quote(self.connection, user_id=UUID(self.user_id), quote_id=UUID(self.quote['id']))
                raise RuntimeError('abort')
        self.assertEqual(self.get(), self.quote)

    def test_concurrent_deletions_have_one_success(self):
        barrier = Barrier(2)

        def remove(_):
            with connect_database(self.database_settings, test=True) as connection:
                connection.execute(sql.SQL('SET search_path TO {}').format(sql.Identifier(self.schema)))
                connection.execute("SET statement_timeout = '10s'")
                barrier.wait(timeout=10)
                try:
                    delete_quote(connection, user_id=UUID(self.user_id), quote_id=UUID(self.quote['id']))
                    return 204
                except DomainError as exc:
                    return exc.status_code

        with ThreadPoolExecutor(max_workers=2) as executor:
            self.assertEqual(sorted(executor.map(remove, range(2))), [204, 404])

    def test_openapi_documents_all_task_8_routes(self):
        paths = self.client.get('/openapi.json').json()['paths']
        self.assertEqual(set(paths['/api/v1/quotes']), {'get', 'post'})
        detail = paths['/api/v1/quotes/{quote_id}']
        self.assertEqual(set(detail), {'get', 'patch', 'delete'})
        for operation in detail.values():
            self.assertEqual(operation['security'], [{'HTTPBearer': []}])
        self.assertNotIn('content', detail['delete']['responses']['204'])

    def test_reads_hold_parent_until_items_are_loaded(self):
        for listing in (False, True):
            parent_loaded, release = Event(), Event()
            load_related = queries._load_related

            def pause_related(*args, **kwargs):
                parent_loaded.set()
                if not release.wait(timeout=10):
                    raise RuntimeError('Read was not released')
                return load_related(*args, **kwargs)

            def read():
                with connect_database(self.database_settings, test=True) as connection:
                    connection.execute(sql.SQL('SET search_path TO {}').format(sql.Identifier(self.schema)))
                    if listing:
                        return queries.paginate_quotes_for_user(connection, user_id=UUID(self.user_id),
                                                               page=1, page_size=20)[0][0]
                    return queries.get_quote_for_user(connection, user_id=UUID(self.user_id),
                                                      quote_id=UUID(self.quote['id']))

            with self.subTest(listing=listing), patch('app.quotes.queries._load_related', side_effect=pause_related), \
                    ThreadPoolExecutor(max_workers=1) as executor:
                future = executor.submit(read)
                try:
                    self.assertTrue(parent_loaded.wait(timeout=10))
                    self.connection.execute("SET lock_timeout = '100ms'")
                    with self.assertRaises(errors.LockNotAvailable):
                        delete_quote(self.connection, user_id=UUID(self.user_id), quote_id=UUID(self.quote['id']))
                finally:
                    release.set()
                    self.connection.execute('SET lock_timeout = 0')
                self.assertEqual(str(future.result(timeout=10).items[0].id), self.quote['items'][0]['id'])
        self.assertEqual(self.delete().status_code, 204)
