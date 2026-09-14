"""Atomic business-profile replacement for an authenticated owner."""

from uuid import UUID

from psycopg import Connection
from psycopg.rows import class_row

from app.business.models import BusinessProfile
from app.business.schemas import BusinessProfilePut


def upsert_profile(
    connection: Connection, *, user_id: UUID, payload: BusinessProfilePut,
) -> BusinessProfile:
    with connection.transaction():
        with connection.cursor(row_factory=class_row(BusinessProfile)) as cursor:
            cursor.execute(
                '''INSERT INTO business_profiles
                   (user_id, business_name, logo_url, email, phone, address, tax_number, default_currency)
                   VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
                   ON CONFLICT (user_id) DO UPDATE SET
                       business_name = EXCLUDED.business_name,
                       logo_url = EXCLUDED.logo_url,
                       email = EXCLUDED.email,
                       phone = EXCLUDED.phone,
                       address = EXCLUDED.address,
                       tax_number = EXCLUDED.tax_number,
                       default_currency = EXCLUDED.default_currency
                   RETURNING id, user_id, business_name, logo_url, email, phone,
                             address, tax_number, default_currency, created_at, updated_at''',
                (user_id, payload.business_name,
                 str(payload.logo_url) if payload.logo_url is not None else None,
                 str(payload.email) if payload.email is not None else None,
                 payload.phone, payload.address, payload.tax_number, payload.default_currency),
            )
            profile = cursor.fetchone()
            if profile is None:
                raise RuntimeError('Business profile upsert returned no row')
            return profile
