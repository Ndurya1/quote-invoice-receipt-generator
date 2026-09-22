"""Typed dashboard summary values."""

from datetime import date, datetime
from decimal import Decimal
from uuid import UUID

from pydantic import BaseModel, ConfigDict


class QuoteSummary(BaseModel):
    model_config = ConfigDict(frozen=True)

    total: int
    draft: int
    sent: int
    accepted: int


class InvoiceSummary(BaseModel):
    model_config = ConfigDict(frozen=True)

    total: int
    draft: int
    sent: int
    paid: int
    overdue: int


class ReceiptSummary(BaseModel):
    model_config = ConfigDict(frozen=True)

    total: int


class RecentDocument(BaseModel):
    model_config = ConfigDict(frozen=True)

    type: str
    id: UUID
    document_number: str
    client_id: UUID
    client_name: str
    issue_date: date
    currency: str
    total: Decimal
    status: str | None
    created_at: datetime


class DashboardSummary(BaseModel):
    model_config = ConfigDict(frozen=True)

    quotes: QuoteSummary
    invoices: InvoiceSummary
    receipts: ReceiptSummary
    recent_documents: tuple[RecentDocument, ...]
