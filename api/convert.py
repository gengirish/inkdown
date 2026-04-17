from http.server import BaseHTTPRequestHandler
import io
import json
import re

from markdown import markdown


# ---------------------------------------------------------------------------
# Backend loader: tries WeasyPrint first, then reportlab
# ---------------------------------------------------------------------------

def load_backend(backend_preference):
    first_error = None

    if backend_preference in ("weasyprint", "auto"):
        try:
            from weasyprint import HTML
            return "weasyprint", HTML
        except (ImportError, OSError) as exc:
            if backend_preference == "weasyprint":
                raise RuntimeError(f"WeasyPrint import failed: {exc}") from exc
            first_error = exc

    if backend_preference in ("reportlab", "auto"):
        try:
            from reportlab.platypus import SimpleDocTemplate
            return "reportlab", SimpleDocTemplate
        except ImportError as exc:
            if backend_preference == "reportlab":
                raise RuntimeError(f"reportlab import failed: {exc}") from exc
            first_error = first_error or exc

    raise RuntimeError(f"No PDF backend available. Last error: {first_error}")


# ---------------------------------------------------------------------------
# WeasyPrint CSS + HTML (unchanged, high-quality HTML->PDF)
# ---------------------------------------------------------------------------

DEFAULT_CSS = """
body {
    font-family: Arial, Helvetica, sans-serif;
    font-size: 11pt;
    line-height: 1.6;
    color: #1f2937;
}
code, pre {
    font-family: Menlo, Monaco, Consolas, 'Courier New', monospace;
    font-size: 9pt;
}
pre {
    background: #f4f4f4;
    padding: 0.75rem 1rem;
    border-radius: 4px;
    overflow-x: auto;
}
code {
    background: #f4f4f4;
    padding: 0.15em 0.35em;
    border-radius: 3px;
}
img { max-width: 100%; }
h1, h2, h3, h4, h5, h6 {
    color: #111827;
    margin-top: 1.5em;
    margin-bottom: 0.5em;
}
h1 { font-size: 22pt; border-bottom: 1px solid #e5e7eb; padding-bottom: 0.3em; }
h2 { font-size: 18pt; border-bottom: 1px solid #e5e7eb; padding-bottom: 0.25em; }
h3 { font-size: 14pt; }
blockquote {
    border-left: 4px solid #cbd5e1;
    margin: 1.5em 0;
    padding: 0.5em 1em;
    color: #475569;
    background: #f8fafc;
}
table {
    width: 100%;
    border-collapse: collapse;
    margin: 1em 0;
    font-size: 10pt;
}
th, td {
    border: 1px solid #d1d5db;
    padding: 6px 10px;
    text-align: left;
}
th { background: #f0f0f0; font-weight: bold; }
tr:nth-child(even) { background: #f8f8f8; }
hr { border: none; border-top: 1px solid #d1d5db; margin: 2em 0; }
"""

HTML_TMPL = """<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8">
<title>{title}</title>
<style>
{css}
</style>
</head>
<body>
{body}
</body>
</html>
"""


def render_html(markdown_text, css_text, title):
    html_body = markdown(
        markdown_text,
        extensions=["extra", "fenced_code", "tables", "toc"],
    )
    return HTML_TMPL.format(title=title, css=css_text, body=html_body)


def build_css(css_text, page_size, margin):
    page_css = f"@page {{ size: {page_size}; margin: {margin}; }}"
    return page_css + "\n" + css_text


# ---------------------------------------------------------------------------
# reportlab backend — Platypus flowables
# ---------------------------------------------------------------------------

PAGE_SIZES = {
    "A4": "A4",
    "A3": "A3",
    "LETTER": "LETTER",
    "LEGAL": "LEGAL",
}


def _parse_margin_pt(margin_text):
    """Convert margin string to points (reportlab native unit)."""
    margin_text = margin_text.strip().lower()
    if margin_text.endswith("in"):
        return float(margin_text[:-2]) * 72
    if margin_text.endswith("mm"):
        return float(margin_text[:-2]) * 2.8346
    if margin_text.endswith("cm"):
        return float(margin_text[:-2]) * 28.346
    if margin_text.endswith("pt"):
        return float(margin_text[:-2])
    return float(margin_text) * 72  # default assume inches


def _get_page_size(name):
    from reportlab.lib.pagesizes import A3, A4, legal, letter
    mapping = {"A4": A4, "A3": A3, "LETTER": letter, "LEGAL": legal}
    return mapping.get(name.upper(), A4)


def _md_inline_to_html(text):
    """Convert markdown inline formatting to reportlab Paragraph XML."""
    text = re.sub(r'\*\*(.+?)\*\*', r'<b>\1</b>', text)
    text = re.sub(r'\*(.+?)\*', r'<i>\1</i>', text)
    text = re.sub(
        r'`([^`]+)`',
        r'<font face="Courier" size="9" color="#c7254e">\1</font>',
        text,
    )
    text = re.sub(
        r'\[([^\]]+)\]\(([^\)]+)\)',
        r'<a href="\2" color="blue"><u>\1</u></a>',
        text,
    )
    # Escape any remaining XML-unsafe characters
    # (but not our tags — only bare & and < that aren't part of tags)
    text = re.sub(r'&(?!amp;|lt;|gt;|quot;|apos;)', '&amp;', text)
    return text


def _strip_inline_md(text):
    """Strip markdown inline markers to get plain text."""
    text = re.sub(r'\*\*([^*]+)\*\*', r'\1', text)
    text = re.sub(r'\*([^*]+)\*', r'\1', text)
    text = re.sub(r'`([^`]+)`', r'\1', text)
    text = re.sub(r'\[([^\]]+)\]\([^\)]+\)', r'\1', text)
    return text.strip()


def _build_reportlab_story(markdown_text, page_width):
    """Parse markdown and return a list of reportlab Platypus flowables."""
    from reportlab.lib import colors
    from reportlab.lib.enums import TA_LEFT
    from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
    from reportlab.lib.units import inch
    from reportlab.platypus import (
        HRFlowable,
        Paragraph,
        Preformatted,
        Spacer,
        Table,
        TableStyle,
    )

    styles = getSampleStyleSheet()

    body_style = ParagraphStyle(
        "MDBody",
        parent=styles["Normal"],
        fontName="Helvetica",
        fontSize=11,
        leading=15,
        textColor=colors.HexColor("#1f2937"),
        spaceAfter=6,
    )
    h_styles = {}
    for level in range(1, 7):
        size = max(22 - (level - 1) * 3, 11)
        h_styles[level] = ParagraphStyle(
            f"MDH{level}",
            parent=styles["Normal"],
            fontName="Helvetica-Bold",
            fontSize=size,
            leading=size * 1.3,
            textColor=colors.HexColor("#111827"),
            spaceBefore=14 if level <= 2 else 8,
            spaceAfter=4,
        )
    code_style = ParagraphStyle(
        "MDCode",
        parent=styles["Normal"],
        fontName="Courier",
        fontSize=9,
        leading=12,
        textColor=colors.HexColor("#1f2937"),
        backColor=colors.HexColor("#f4f4f4"),
        leftIndent=8,
        rightIndent=8,
        spaceBefore=2,
        spaceAfter=2,
    )
    blockquote_style = ParagraphStyle(
        "MDBlockquote",
        parent=styles["Normal"],
        fontName="Helvetica-Oblique",
        fontSize=10,
        leading=14,
        textColor=colors.HexColor("#475569"),
        leftIndent=16,
        borderColor=colors.HexColor("#cbd5e1"),
        borderWidth=0,
        spaceAfter=8,
    )
    bullet_style = ParagraphStyle(
        "MDBullet",
        parent=body_style,
        leftIndent=20,
        bulletIndent=8,
        spaceAfter=3,
    )
    numbered_style = ParagraphStyle(
        "MDNumbered",
        parent=body_style,
        leftIndent=20,
        bulletIndent=4,
        spaceAfter=3,
    )

    table_header_style = ParagraphStyle(
        "MDTableHeader",
        parent=styles["Normal"],
        fontName="Helvetica-Bold",
        fontSize=9,
        leading=12,
        alignment=TA_LEFT,
    )
    table_cell_style = ParagraphStyle(
        "MDTableCell",
        parent=styles["Normal"],
        fontName="Helvetica",
        fontSize=9,
        leading=12,
        alignment=TA_LEFT,
    )

    usable_width = page_width

    story = []
    lines = markdown_text.splitlines()
    i = 0
    in_code_block = False
    code_lines = []
    table_buffer = []

    def flush_table():
        nonlocal table_buffer
        if len(table_buffer) < 2:
            table_buffer = []
            return

        header_cells = [c.strip() for c in table_buffer[0].strip('|').split('|')]
        col_count = len(header_cells)
        data_rows = []
        for row_line in table_buffer[1:]:
            stripped = row_line.strip('|').strip()
            if re.match(r'^[\s|:\-]+$', stripped):
                continue
            cells = [c.strip() for c in row_line.strip('|').split('|')]
            while len(cells) < col_count:
                cells.append('')
            data_rows.append(cells[:col_count])
        table_buffer = []

        if not data_rows:
            return

        header_paras = [
            Paragraph(_md_inline_to_html(c), table_header_style)
            for c in header_cells
        ]
        body_paras = []
        for row in data_rows:
            body_paras.append([
                Paragraph(_md_inline_to_html(c), table_cell_style)
                for c in row
            ])

        table_data = [header_paras] + body_paras

        col_widths = [usable_width / col_count] * col_count

        t_style_cmds = [
            ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#f0f0f0")),
            ("TEXTCOLOR", (0, 0), (-1, 0), colors.HexColor("#111827")),
            ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
            ("FONTSIZE", (0, 0), (-1, -1), 9),
            ("GRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#d1d5db")),
            ("VALIGN", (0, 0), (-1, -1), "TOP"),
            ("TOPPADDING", (0, 0), (-1, -1), 4),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
            ("LEFTPADDING", (0, 0), (-1, -1), 6),
            ("RIGHTPADDING", (0, 0), (-1, -1), 6),
        ]
        for row_idx in range(1, len(table_data)):
            if row_idx % 2 == 0:
                t_style_cmds.append(
                    ("BACKGROUND", (0, row_idx), (-1, row_idx), colors.HexColor("#f8f8f8"))
                )

        tbl = Table(table_data, colWidths=col_widths, repeatRows=1)
        tbl.setStyle(TableStyle(t_style_cmds))
        story.append(Spacer(1, 4))
        story.append(tbl)
        story.append(Spacer(1, 6))

    while i < len(lines):
        line = lines[i]

        # --- code fence ---
        if line.startswith("```"):
            if in_code_block:
                code_text = "\n".join(code_lines)
                story.append(Preformatted(code_text, code_style))
                story.append(Spacer(1, 4))
                code_lines = []
                in_code_block = False
            else:
                if table_buffer:
                    flush_table()
                in_code_block = True
            i += 1
            continue

        if in_code_block:
            code_lines.append(line)
            i += 1
            continue

        # --- table row ---
        if re.match(r'^\s*\|', line):
            table_buffer.append(line)
            i += 1
            continue
        elif table_buffer:
            flush_table()

        # --- blank line ---
        if not line.strip():
            story.append(Spacer(1, 6))
            i += 1
            continue

        # --- horizontal rule ---
        if re.match(r'^-{3,}$|^\*{3,}$|^_{3,}$', line.strip()):
            story.append(Spacer(1, 6))
            story.append(
                HRFlowable(
                    width="100%",
                    thickness=0.5,
                    color=colors.HexColor("#d1d5db"),
                    spaceAfter=6,
                    spaceBefore=6,
                )
            )
            i += 1
            continue

        # --- heading ---
        heading = re.match(r"^(#{1,6})\s+(.*)", line)
        if heading:
            level = len(heading.group(1))
            text = _md_inline_to_html(heading.group(2).strip())
            story.append(Paragraph(text, h_styles[level]))
            if level <= 2:
                story.append(
                    HRFlowable(
                        width="100%",
                        thickness=0.3,
                        color=colors.HexColor("#e5e7eb"),
                        spaceAfter=4,
                    )
                )
            i += 1
            continue

        # --- blockquote ---
        bq = re.match(r"^>\s+(.*)", line)
        if bq:
            text = _md_inline_to_html(bq.group(1).strip())
            story.append(Paragraph(text, blockquote_style))
            i += 1
            continue

        # --- numbered list ---
        numbered = re.match(r'^(\d+)\.\s+(.*)', line)
        if numbered:
            text = _md_inline_to_html(numbered.group(2).strip())
            bullet_text = f"{numbered.group(1)}."
            story.append(
                Paragraph(
                    text,
                    numbered_style,
                    bulletText=bullet_text,
                )
            )
            i += 1
            continue

        # --- bullet list ---
        list_item = re.match(r"^([-*+])\s+(.*)", line)
        if list_item:
            text = _md_inline_to_html(list_item.group(2).strip())
            story.append(
                Paragraph(text, bullet_style, bulletText="\u2022")
            )
            i += 1
            continue

        # --- normal paragraph ---
        text = _md_inline_to_html(line)
        story.append(Paragraph(text, body_style))
        i += 1

    # flush remaining
    if code_lines:
        story.append(Preformatted("\n".join(code_lines), code_style))
    if table_buffer:
        flush_table()

    return story


def write_pdf_reportlab(content, page_size_name, margin_str, title):
    """Generate PDF bytes using reportlab Platypus."""
    from reportlab.platypus import SimpleDocTemplate

    buf = io.BytesIO()
    ps = _get_page_size(page_size_name)
    margin_pt = _parse_margin_pt(margin_str)

    doc = SimpleDocTemplate(
        buf,
        pagesize=ps,
        title=title,
        topMargin=margin_pt,
        bottomMargin=margin_pt,
        leftMargin=margin_pt,
        rightMargin=margin_pt,
    )

    usable_width = ps[0] - 2 * margin_pt
    story = _build_reportlab_story(content, usable_width)
    doc.build(story)
    return buf.getvalue()


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def write_pdf(content, backend_name, backend_module, page_size="A4", margin="1in", title="Markdown Document"):
    if backend_name == "weasyprint":
        css_text = build_css(DEFAULT_CSS, page_size, margin)
        html = render_html(content, css_text, title)
        return backend_module(string=html).write_pdf()

    if backend_name == "reportlab":
        return write_pdf_reportlab(content, page_size, margin, title)

    raise RuntimeError(f"Unsupported backend: {backend_name}")


def convert_markdown_to_pdf(markdown_text, page_size='A4', margin='1in'):
    backend_name, backend_module = load_backend("auto")
    return write_pdf(markdown_text, backend_name, backend_module, page_size=page_size, margin=margin)


# ---------------------------------------------------------------------------
# Vercel serverless handler
# ---------------------------------------------------------------------------

class handler(BaseHTTPRequestHandler):

    def _send_json(self, status, data):
        body = json.dumps(data).encode('utf-8')
        self.send_response(status)
        self.send_header('Content-Type', 'application/json')
        self.send_header('Content-Length', str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def do_POST(self):
        try:
            content_length = int(self.headers.get('Content-Length', 0))
            raw = self.rfile.read(content_length)
            body = json.loads(raw)
        except (json.JSONDecodeError, ValueError):
            self._send_json(400, {'error': 'Invalid JSON body'})
            return

        markdown_text = body.get('markdown', '')
        page_size = body.get('page_size', 'A4')
        margin = body.get('margin', '1in')

        if not markdown_text.strip():
            self._send_json(400, {'error': 'No markdown content provided'})
            return

        try:
            pdf_bytes = convert_markdown_to_pdf(markdown_text, page_size=page_size, margin=margin)
        except Exception as e:
            self._send_json(500, {'error': str(e)})
            return

        self.send_response(200)
        self.send_header('Content-Type', 'application/pdf')
        self.send_header('Content-Disposition', 'attachment; filename="converted.pdf"')
        self.send_header('Content-Length', str(len(pdf_bytes)))
        self.end_headers()
        self.wfile.write(pdf_bytes)

    def do_GET(self):
        self._send_json(405, {'error': 'Method not allowed'})

    def do_OPTIONS(self):
        self.send_response(204)
        self.send_header('Allow', 'POST, OPTIONS')
        self.end_headers()
