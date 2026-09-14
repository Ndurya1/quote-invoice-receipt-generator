import unittest
from datetime import timedelta
from uuid import UUID, uuid4

from psycopg import errors
from psycopg.rows import class_row

from app.accounts.service import create_user
from app.clients.models import Client
from tests import test_accounts


class ClientPersistenceTests(unittest.TestCase):
    setUpClass = classmethod(test_accounts.UserPersistenceTests.setUpClass.__func__)
    setUp = test_accounts.UserPersistenceTests.setUp
    drop_test_schema = test_accounts.UserPersistenceTests.drop_test_schema

    def create_owner(self, email='owner@example.com'):
        return create_user(self.connection, name='Owner', email=email, password='test-password')

    def insert_client(self, user_id, name='Client', email=None, phone=None, address=None):
        with self.connection.cursor(row_factory=class_row(Client)) as cursor:
            cursor.execute(
                'INSERT INTO clients (user_id, name, email, phone, address) '
                'VALUES (%s, %s, %s, %s, %s) RETURNING *',
                (user_id, name, email, phone, address),
            )
            return cursor.fetchone()

    def test_creation_has_uuid_utc_timestamps_and_nullable_contacts(self):
        owner = self.create_owner()
        client = self.insert_client(owner.id)
        self.assertIsInstance(client, Client)
        self.assertIsInstance(client.id, UUID)
        self.assertEqual(client.user_id, owner.id)
        self.assertEqual(client.name, 'Client')
        for field in ('email', 'phone', 'address'):
            self.assertIsNone(getattr(client, field))
        self.assertEqual(client.created_at.utcoffset(), timedelta(0))
        self.assertEqual(client.created_at, client.updated_at)

    def test_full_row_and_update_timestamp(self):
        owner = self.create_owner()
        client = self.insert_client(owner.id, "O'Brien", 'client@example.com', '+254700123456', 'Nairobi')
        self.assertEqual(client.model_dump(exclude={'id', 'created_at', 'updated_at'}), {
            'user_id': owner.id, 'name': "O'Brien", 'email': 'client@example.com',
            'phone': '+254700123456', 'address': 'Nairobi',
        })
        with self.connection.cursor(row_factory=class_row(Client)) as cursor:
            cursor.execute('UPDATE clients SET name = %s WHERE id = %s RETURNING *',
                           ('Updated', client.id))
            updated = cursor.fetchone()
        self.assertEqual(updated.id, client.id)
        self.assertEqual(updated.created_at, client.created_at)
        self.assertGreater(updated.updated_at, client.updated_at)

    def test_name_and_existing_owner_are_required(self):
        owner = self.create_owner()
        for user_id, name in ((owner.id, None), (None, 'Client')):
            with self.subTest(user_id=user_id, name=name), self.assertRaises(errors.NotNullViolation):
                self.insert_client(user_id, name)
        with self.assertRaises(errors.NotNullViolation):
            self.connection.execute('INSERT INTO clients (user_id) VALUES (%s)', (owner.id,))
        with self.assertRaises(errors.ForeignKeyViolation):
            self.insert_client(uuid4())
        with self.assertRaises(errors.StringDataRightTruncation):
            self.insert_client(owner.id, 'x' * 161)
        self.assertEqual(self.insert_client(owner.id, 'x' * 160).name, 'x' * 160)

    def test_duplicate_emails_allowed_within_and_across_owners(self):
        first_owner = self.create_owner()
        second_owner = self.create_owner('other@example.com')
        clients = [self.insert_client(owner_id, email='shared@example.com')
                   for owner_id in (first_owner.id, first_owner.id, second_owner.id)]
        self.assertEqual(len({client.id for client in clients}), 3)
        self.assertEqual(self.connection.execute('SELECT count(*) FROM clients').fetchone()[0], 3)

    def test_documented_owner_indexes_exist(self):
        indexes = dict(self.connection.execute(
            "SELECT indexname, indexdef FROM pg_indexes WHERE schemaname = current_schema() AND tablename = 'clients'"
        ).fetchall())
        self.assertIn('(user_id)', indexes['clients_user_id_idx'])
        self.assertIn('(user_id, name)', indexes['clients_user_name_idx'])
