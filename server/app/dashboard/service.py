"""Dashboard summary orchestration."""

from uuid import UUID

from psycopg import Connection

from app.dashboard.models import DashboardSummary
from app.dashboard.queries import (
    fetch_invoice_summary,
    fetch_quote_summary,
    fetch_receipt_summary,
    fetch_recent_documents,
)


def get_dashboard_summary(connection: Connection, *, user_id: UUID) -> DashboardSummary:
    """Build one consistent, owner-scoped dashboard snapshot."""
    with connection.transaction():
        return DashboardSummary(
            quotes=fetch_quote_summary(connection, user_id=user_id),
            invoices=fetch_invoice_summary(connection, user_id=user_id),
            receipts=fetch_receipt_summary(connection, user_id=user_id),
            recent_documents=fetch_recent_documents(connection, user_id=user_id),
        )
