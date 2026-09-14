import unittest
import tempfile
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor
from threading import Barrier

from psycopg import errors, sql

from app.accounts.service import create_user
from app.common.database import connect_database
from app.common.numbering import next_receipt_number, next_quote_number, next_invoice_number
from app.common.errors import DomainError
from app.common.migrations import MIGRATIONS_DIRECTORY, apply_migrations
from tests import test_accounts


class ReceiptNumberingTests(unittest.TestCase):
    setUpClass = classmethod(test_accounts.UserPersistenceTests.setUpClass.__func__)
    setUp = test_accounts.UserPersistenceTests.setUp
    drop_test_schema = test_accounts.UserPersistenceTests.drop_test_schema

    def owner(self, email='owner@example.com'):
        return create_user(self.connection, name='Owner', email=email, password='test-password')

    def test_upgrade_seeds_existing_receipt_numbers(self):
        upgrade_schema = self.schema + '_upgrade'
        self.connection.execute(sql.SQL('CREATE SCHEMA {}').format(sql.Identifier(upgrade_schema)))
        try:
            self.connection.execute(sql.SQL('SET search_path TO {}').format(sql.Identifier(upgrade_schema)))
            with tempfile.TemporaryDirectory() as temp:
                directory = Path(temp)
                (directory / '001_initial.sql').write_text(
                    (MIGRATIONS_DIRECTORY / '001_initial.sql').read_text(encoding='utf-8'), encoding='utf-8')
                apply_migrations(self.connection, directory)
            owner = self.owner()
            client_id = self.connection.execute(
                "INSERT INTO clients (user_id, name) VALUES (%s, 'Client') RETURNING id", (owner.id,),
            ).fetchone()[0]
            for number in ('RCT-0003', 'RCT-0012', 'LEGACY-99'):
                self.connection.execute(
                    '''INSERT INTO receipts (user_id, client_id, receipt_number, issue_date, currency, subtotal, total)
                       VALUES (%s, %s, %s, CURRENT_DATE, 'KES', 0, 0)''', (owner.id, client_id, number))
            self.assertEqual(apply_migrations(self.connection),
                             sorted(p.name for p in MIGRATIONS_DIRECTORY.glob('*.sql') if p.name > '001_initial.sql'))
            self.assertEqual(next_receipt_number(self.connection, user_id=owner.id), 'RCT-0013')
        finally:
            self.connection.execute(sql.SQL('SET search_path TO {}').format(sql.Identifier(self.schema)))
            self.connection.execute(sql.SQL('DROP SCHEMA {} CASCADE').format(sql.Identifier(upgrade_schema)))

    def test_sequences_are_independent_and_expand_past_four_digits(self):
        first, second = self.owner(), self.owner('other@example.com')
        self.assertEqual(next_receipt_number(self.connection, user_id=first.id), 'RCT-0001')
        self.assertEqual(next_receipt_number(self.connection, user_id=first.id), 'RCT-0002')
        self.assertEqual(next_receipt_number(self.connection, user_id=second.id), 'RCT-0001')
        self.connection.execute('UPDATE receipt_number_counters SET last_number = 9999 WHERE user_id = %s', (first.id,))
        self.assertEqual(next_receipt_number(self.connection, user_id=first.id), 'RCT-10000')

    def test_receipt_sequence_is_independent_of_quotes_and_invoices(self):
        owner = self.owner()
        self.assertEqual(next_quote_number(self.connection, user_id=owner.id), 'QT-0001')
        self.assertEqual(next_quote_number(self.connection, user_id=owner.id), 'QT-0002')
        self.assertEqual(next_receipt_number(self.connection, user_id=owner.id), 'RCT-0001')
        self.assertEqual(next_invoice_number(self.connection, user_id=owner.id), 'INV-0001')
        self.assertEqual(next_receipt_number(self.connection, user_id=owner.id), 'RCT-0002')
        self.assertEqual(next_quote_number(self.connection, user_id=owner.id), 'QT-0003')

    def test_exhaustion_returns_conflict_without_changing_counter(self):
        owner = self.owner()
        self.connection.execute('INSERT INTO receipt_number_counters VALUES (%s, 9223372036854775807)', (owner.id,))
        with self.assertRaises(DomainError) as error:
            next_receipt_number(self.connection, user_id=owner.id)
        self.assertEqual(error.exception.code, 'RECEIPT_NUMBER_EXHAUSTED')
        self.assertEqual(error.exception.status_code, 409)
        self.assertEqual(self.connection.execute('SELECT last_number FROM receipt_number_counters WHERE user_id = %s',
                                                (owner.id,)).fetchone()[0], 9223372036854775807)

    def test_concurrent_first_allocations_are_unique(self):
        owner = self.owner()
        barrier = Barrier(6)

        def allocate(_):
            with connect_database(self.settings, test=True) as connection:
                connection.execute(sql.SQL('SET search_path TO {}').format(sql.Identifier(self.schema)))
                connection.execute("SET statement_timeout = '10s'")
                barrier.wait(timeout=10)
                return next_receipt_number(connection, user_id=owner.id)

        with ThreadPoolExecutor(max_workers=6) as executor:
            numbers = list(executor.map(allocate, range(6)))
        self.assertEqual(sorted(numbers), [f'RCT-{i:04d}' for i in range(1, 7)])

    def test_rollback_restores_both_new_and_existing_counter(self):
        owner = self.owner()
        for expected in ('RCT-0001', 'RCT-0002'):
            with self.assertRaisesRegex(RuntimeError, 'abort'):
                with self.connection.transaction():
                    self.assertEqual(next_receipt_number(self.connection, user_id=owner.id), expected)
                    raise RuntimeError('abort')
            self.assertEqual(next_receipt_number(self.connection, user_id=owner.id), expected)

    def test_persisted_number_is_immutable_and_deletion_does_not_reuse_it(self):
        owner = self.owner()
        client_id = self.connection.execute(
            "INSERT INTO clients (user_id, name) VALUES (%s, 'Client') RETURNING id", (owner.id,),
        ).fetchone()[0]
        with self.connection.transaction():
            number = next_receipt_number(self.connection, user_id=owner.id)
            receipt_id = self.connection.execute(
                '''INSERT INTO receipts (user_id, client_id, receipt_number, issue_date, currency, subtotal, total)
                   VALUES (%s, %s, %s, CURRENT_DATE, 'KES', 0, 0) RETURNING id''',
                (owner.id, client_id, number),
            ).fetchone()[0]
        with self.assertRaises(errors.CheckViolation):
            self.connection.execute("UPDATE receipts SET receipt_number = 'RCT-9999' WHERE id = %s", (receipt_id,))
        self.connection.execute("UPDATE receipts SET notes = 'Updated' WHERE id = %s", (receipt_id,))
        self.assertEqual(self.connection.execute('SELECT receipt_number FROM receipts WHERE id = %s', (receipt_id,)).fetchone()[0], number)
        self.connection.execute('DELETE FROM receipts WHERE id = %s', (receipt_id,))
        self.assertEqual(next_receipt_number(self.connection, user_id=owner.id), 'RCT-0002')


