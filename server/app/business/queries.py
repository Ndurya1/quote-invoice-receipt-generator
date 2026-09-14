"""Business-profile reads scoped to an authenticated owner."""

from uuid import UUID

from psycopg import Connection
from psycopg.rows import class_row

from app.business.models import BusinessProfile


def get_profile_for_user(connection: Connection, user_id: UUID) -> BusinessProfile | None:
    with connection.cursor(row_factory=class_row(BusinessProfile)) as cursor:
        cursor.execute(
            'SELECT id, user_id, business_name, logo_url, email, phone, address, '
            'tax_number, default_currency, created_at, updated_at '
            'FROM business_profiles WHERE user_id = %s',
            (user_id,),
        )
        return cursor.fetchone()
