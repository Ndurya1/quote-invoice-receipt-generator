"""Receipt PDF renderer."""

from app.pdf.models import DocumentRenderContext
from app.pdf.rendering import render_document_pdf


def render_receipt_pdf(context: DocumentRenderContext) -> bytes:
    return render_document_pdf(context)
