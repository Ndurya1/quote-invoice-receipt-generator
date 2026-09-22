"""Owner-scoped dashboard aggregation queries."""

from uuid import UUID

from psycopg import Connection
from psycopg.rows import class_row

from app.dashboard.models import InvoiceSummary, QuoteSummary, RecentDocument, ReceiptSummary


def fetch_quote_summary(connection: Connection, *, user_id: UUID) -> QuoteSummary:
    row = connection.execute(
        """SELECT count(*) AS total,
                   count(*) FILTER (WHERE status = 'DRAFT') AS draft,
                   count(*) FILTER (WHERE status = 'SENT') AS sent,
                   count(*) FILTER (WHERE status = 'ACCEPTED') AS accepted
            FROM quotes
            WHERE user_id = %s""",
        (user_id,),
    ).fetchone()
    return QuoteSummary(**dict(zip(('total', 'draft', 'sent', 'accepted'), row)))


def fetch_invoice_summary(connection: Connection, *, user_id: UUID) -> InvoiceSummary:
    row = connection.execute(
        """SELECT count(*) AS total,
                   count(*) FILTER (WHERE status = 'DRAFT') AS draft,
                   count(*) FILTER (WHERE status = 'SENT') AS sent,
                   count(*) FILTER (WHERE status = 'PAID') AS paid,
                   count(*) FILTER (WHERE status = 'OVERDUE') AS overdue
            FROM invoices
            WHERE user_id = %s""",
        (user_id,),
    ).fetchone()
    return InvoiceSummary(**dict(zip(('total', 'draft', 'sent', 'paid', 'overdue'), row)))


def fetch_receipt_summary(connection: Connection, *, user_id: UUID) -> ReceiptSummary:
    total = connection.execute(
        'SELECT count(*) FROM receipts WHERE user_id = %s', (user_id,),
    ).fetchone()[0]
    return ReceiptSummary(total=total)


def fetch_recent_documents(
    connection: Connection, *, user_id: UUID, limit: int = 5,
) -> tuple[RecentDocument, ...]:
    if limit < 1:
        raise ValueError('Recent document limit must be positive')
    query = """
        SELECT 'quote' AS type, q.id, q.quote_number AS document_number,
               q.client_id, c.name AS client_name, q.issue_date, q.currency,
               q.total, q.status::text AS status, q.created_at
        FROM quotes q
        JOIN clients c ON c.id = q.client_id AND c.user_id = q.user_id
        WHERE q.user_id = %s
        UNION ALL
        SELECT 'invoice' AS type, i.id, i.invoice_number AS document_number,
               i.client_id, c.name AS client_name, i.issue_date, i.currency,
               i.total, i.status::text AS status, i.created_at
        FROM invoices i
        JOIN clients c ON c.id = i.client_id AND c.user_id = i.user_id
        WHERE i.user_id = %s
        UNION ALL
        SELECT 'receipt' AS type, r.id, r.receipt_number AS document_number,
               r.client_id, c.name AS client_name, r.issue_date, r.currency,
               r.total, NULL::text AS status, r.created_at
        FROM receipts r
        JOIN clients c ON c.id = r.client_id AND c.user_id = r.user_id
        WHERE r.user_id = %s
        ORDER BY created_at DESC, id DESC
        LIMIT %s
    """
    with connection.cursor(row_factory=class_row(RecentDocument)) as cursor:
        cursor.execute(query, (user_id, user_id, user_id, limit))
        return tuple(cursor.fetchall())
