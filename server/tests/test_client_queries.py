import unittest
from datetime import timedelta
from uuid import UUID, uuid4

from psycopg import errors

from app.accounts.service import create_user
from app.clients.models import Client
from app.clients.queries import get_client_for_user, list_clients_for_user
from tests import test_accounts


class ClientQueryTests(unittest.TestCase):
    setUpClass = classmethod(test_accounts.UserPersistenceTests.setUpClass.__func__)
    setUp = test_accounts.UserPersistenceTests.setUp
    drop_test_schema = test_accounts.UserPersistenceTests.drop_test_schema

    def owner(self, email='owner@example.com'):
        return create_user(self.connection, name='Owner', email=email, password='test-password')

    def insert(self, user_id, name='Client'):
        return self.connection.execute(
            'INSERT INTO clients (user_id, name) VALUES (%s, %s) RETURNING id',
            (user_id, name),
        ).fetchone()[0]

    def test_own_client_returns_typed_persisted_fields(self):
        owner = self.owner()
        client_id = self.insert(owner.id, "O'Brien")
        client = get_client_for_user(self.connection, user_id=owner.id, client_id=client_id)
        self.assertIsInstance(client, Client)
        self.assertIsInstance(client.id, UUID)
        self.assertEqual(client.id, client_id)
        self.assertEqual(client.user_id, owner.id)
        self.assertEqual(client.name, "O'Brien")
        for field in ('email', 'phone', 'address'):
            self.assertIsNone(getattr(client, field))
        self.assertEqual(client.created_at.utcoffset(), timedelta(0))
        self.assertEqual(client.created_at, client.updated_at)
        self.connection.execute('UPDATE clients SET email = %s, phone = %s, address = %s WHERE id = %s',
                                ('client@example.com', '+254700123456', 'Nairobi', client_id))
        updated = get_client_for_user(self.connection, user_id=owner.id, client_id=client_id)
        self.assertEqual((updated.email, updated.phone, updated.address),
                         ('client@example.com', '+254700123456', 'Nairobi'))

    def test_foreign_and_missing_clients_both_return_none(self):
        first, second = self.owner(), self.owner('other@example.com')
        client_id = self.insert(second.id)
        for owner_id, requested_id in ((first.id, client_id), (second.id, uuid4()), (uuid4(), client_id)):
            with self.subTest(owner_id=owner_id, client_id=requested_id):
                self.assertIsNone(get_client_for_user(self.connection, user_id=owner_id, client_id=requested_id))
        self.assertEqual(get_client_for_user(self.connection, user_id=second.id, client_id=client_id).id, client_id)

    def test_lists_are_isolated_and_order_ties_by_uuid(self):
        first, second = self.owner(), self.owner('other@example.com')
        with self.connection.transaction():
            first_ids = [self.insert(first.id, 'Same name') for _ in range(2)]
            second_id = self.insert(second.id, 'Same name')
        clients = list_clients_for_user(self.connection, user_id=first.id)
        self.assertEqual([client.id for client in clients], sorted(first_ids))
        self.assertTrue(all(client.user_id == first.id for client in clients))
        self.assertEqual([client.id for client in list_clients_for_user(self.connection, user_id=second.id)], [second_id])
        self.assertEqual(list_clients_for_user(self.connection, user_id=uuid4()), [])

    def test_required_name_and_duplicate_emails_in_existing_table(self):
        owner = self.owner()
        with self.assertRaises(errors.NotNullViolation):
            self.insert(owner.id, None)
        ids = [self.insert(owner.id) for _ in range(2)]
        self.connection.execute('UPDATE clients SET email = %s WHERE user_id = %s', ('shared@example.com', owner.id))
        clients = list_clients_for_user(self.connection, user_id=owner.id)
        self.assertEqual({client.id for client in clients}, set(ids))
        self.assertTrue(all(client.email == 'shared@example.com' for client in clients))
