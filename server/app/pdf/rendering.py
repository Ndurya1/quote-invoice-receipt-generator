"""Shared ReportLab document rendering primitives."""

from io import BytesIO
from xml.sax.saxutils import escape

from reportlab.lib import colors
from reportlab.lib.enums import TA_RIGHT
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import mm
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle

from app.pdf.models import DocumentRenderContext


def _text(value: object) -> str:
    return escape(str(value))


def _money(context: DocumentRenderContext, value: object) -> str:
    return f'{context.currency} {_text(value)}'


def _styles():
    styles = getSampleStyleSheet()
    styles.add(ParagraphStyle(
        name='DocumentTitle', parent=styles['Title'], fontName='Helvetica-Bold',
        fontSize=20, leading=24, textColor=colors.HexColor('#17324D'), spaceAfter=4,
    ))
    styles.add(ParagraphStyle(
        name='DocumentHeading', parent=styles['Heading2'], fontName='Helvetica-Bold',
        fontSize=10, leading=12, textColor=colors.HexColor('#17324D'), spaceBefore=8,
        spaceAfter=4,
    ))
    styles.add(ParagraphStyle(
        name='SmallText', parent=styles['BodyText'], fontSize=8, leading=10,
        textColor=colors.HexColor('#4B5563'),
    ))
    styles.add(ParagraphStyle(
        name='RightSmallText', parent=styles['SmallText'], alignment=TA_RIGHT,
    ))
    return styles


def _paragraph(value: object, style) -> Paragraph:
    return Paragraph(_text(value), style)


def _header(context: DocumentRenderContext, styles):
    business = context.business
    business_name = business.business_name if business else 'Business'
    business_lines = [business_name]
    if business:
        business_lines.extend(value for value in (business.address, business.email, business.phone) if value)
    business_block = Paragraph('<br/>'.join(_text(value) for value in business_lines), styles['BodyText'])
    title = Paragraph(context.document_type.upper(), styles['DocumentTitle'])
    number = Paragraph(f'<b>{_text(context.document_number)}</b>', styles['SmallText'])
    table = Table([[business_block, [title, number]]], colWidths=[105 * mm, 75 * mm])
    table.setStyle(TableStyle([
        ('VALIGN', (0, 0), (-1, -1), 'TOP'),
        ('ALIGN', (1, 0), (1, 0), 'RIGHT'),
        ('LEFTPADDING', (0, 0), (-1, -1), 0),
        ('RIGHTPADDING', (0, 0), (-1, -1), 0),
        ('TOPPADDING', (0, 0), (-1, -1), 0),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 0),
    ]))
    return table


def _metadata(context: DocumentRenderContext, styles):
    date_label = 'Expiry date' if context.document_type == 'quote' else 'Due date'
    rows = [
        [_paragraph('Client', styles['SmallText']), _paragraph('Issue date', styles['SmallText']),
         _paragraph(date_label, styles['SmallText']), _paragraph('Status', styles['SmallText'])],
        [_paragraph(context.client.name, styles['BodyText']), _paragraph(context.issue_date, styles['BodyText']),
         _paragraph(context.secondary_date or '—', styles['BodyText']),
         _paragraph(context.status or 'Issued', styles['BodyText'])],
    ]
    table = Table(rows, colWidths=[75 * mm, 35 * mm, 35 * mm, 35 * mm])
    table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#F3F6F9')),
        ('BOX', (0, 0), (-1, -1), 0.5, colors.HexColor('#D5DDE5')),
        ('INNERGRID', (0, 0), (-1, -1), 0.25, colors.HexColor('#D5DDE5')),
        ('VALIGN', (0, 0), (-1, -1), 'TOP'),
        ('LEFTPADDING', (0, 0), (-1, -1), 7),
        ('RIGHTPADDING', (0, 0), (-1, -1), 7),
        ('TOPPADDING', (0, 0), (-1, -1), 5),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 5),
    ]))
    return table


def _items(context: DocumentRenderContext, styles):
    rows = [[
        _paragraph('Description', styles['SmallText']),
        _paragraph('Quantity', styles['RightSmallText']),
        _paragraph('Unit price', styles['RightSmallText']),
        _paragraph('Amount', styles['RightSmallText']),
    ]]
    for item in context.items:
        rows.append([
            _paragraph(item.description, styles['BodyText']),
            _paragraph(item.quantity, styles['RightSmallText']),
            _paragraph(_money(context, item.unit_price), styles['RightSmallText']),
            _paragraph(_money(context, item.line_total), styles['RightSmallText']),
        ])
    table = Table(rows, colWidths=[85 * mm, 25 * mm, 35 * mm, 35 * mm], repeatRows=1)
    table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#17324D')),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
        ('BOX', (0, 0), (-1, -1), 0.5, colors.HexColor('#D5DDE5')),
        ('INNERGRID', (0, 0), (-1, -1), 0.25, colors.HexColor('#E5E7EB')),
        ('VALIGN', (0, 0), (-1, -1), 'TOP'),
        ('LEFTPADDING', (0, 0), (-1, -1), 7),
        ('RIGHTPADDING', (0, 0), (-1, -1), 7),
        ('TOPPADDING', (0, 0), (-1, -1), 6),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
    ]))
    return table


def _totals(context: DocumentRenderContext, styles):
    rows = [
        ['Subtotal', _money(context, context.subtotal)],
        [f'Tax ({context.tax_rate}%)', _money(context, context.tax_amount)],
        ['Discount', _money(context, context.discount_amount)],
        ['Total', _money(context, context.total)],
    ]
    table = Table([[Paragraph(_text(label), styles['BodyText']),
                    Paragraph(_text(value), styles['RightSmallText'])]
                   for label, value in rows], colWidths=[145 * mm, 35 * mm])
    table.setStyle(TableStyle([
        ('LINEABOVE', (0, -1), (-1, -1), 1, colors.HexColor('#17324D')),
        ('FONTNAME', (0, -1), (-1, -1), 'Helvetica-Bold'),
        ('FONTSIZE', (0, -1), (-1, -1), 11),
        ('LEFTPADDING', (0, 0), (-1, -1), 7),
        ('RIGHTPADDING', (0, 0), (-1, -1), 7),
        ('TOPPADDING', (0, 0), (-1, -1), 4),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 4),
    ]))
    return table


def render_document_pdf(context: DocumentRenderContext) -> bytes:
    buffer = BytesIO()
    document = SimpleDocTemplate(
        buffer, pagesize=A4, rightMargin=15 * mm, leftMargin=15 * mm,
        topMargin=15 * mm, bottomMargin=15 * mm, title=context.document_number,
        author=context.business.business_name if context.business else 'Business',
        pageCompression=0,
    )
    styles = _styles()
    story = [_header(context, styles), Spacer(1, 10 * mm), _metadata(context, styles),
             Spacer(1, 10 * mm), _items(context, styles), Spacer(1, 8 * mm),
             _totals(context, styles)]
    if context.notes:
        story.extend([Spacer(1, 8 * mm), Paragraph('Notes', styles['DocumentHeading']),
                      Paragraph(_text(context.notes), styles['BodyText'])])
    if context.terms:
        story.extend([Spacer(1, 5 * mm), Paragraph('Terms', styles['DocumentHeading']),
                      Paragraph(_text(context.terms), styles['BodyText'])])
    document.build(story)
    return buffer.getvalue()
