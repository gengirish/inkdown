from http.server import BaseHTTPRequestHandler
import json
import re

from markdown import markdown

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

    if backend_preference in ("fpdf", "auto"):
        try:
            from fpdf import FPDF
            return "fpdf", FPDF
        except ImportError as exc:
            if backend_preference == "fpdf":
                raise RuntimeError(f"fpdf2 import failed: {exc}") from exc
            first_error = first_error or exc

    raise RuntimeError(f"No PDF backend available. Last error: {first_error}")

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
img {
    max-width: 100%;
}
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
th {
    background: #f0f0f0;
    font-weight: bold;
}
tr:nth-child(even) {
    background: #f8f8f8;
}
hr {
    border: none;
    border-top: 1px solid #d1d5db;
    margin: 2em 0;
}
"""

HTML_TMPL = """<!DOCTYPE html>
<html lang=\"en\">
<head>
<meta charset=\"utf-8\">
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

def parse_margin(margin_text):
    margin_text = margin_text.strip().lower()
    if margin_text.endswith("in"):
        return float(margin_text[:-2]) * 25.4
    if margin_text.endswith("mm"):
        return float(margin_text[:-2])
    if margin_text.endswith("cm"):
        return float(margin_text[:-2]) * 10.0
    if margin_text.endswith("pt"):
        return float(margin_text[:-2]) * 0.352778
    return float(margin_text)

def render_html(markdown_text, css_text, title):
    html_body = markdown(markdown_text, extensions=["extra", "fenced_code", "tables", "toc"])
    return HTML_TMPL.format(title=title, css=css_text, body=html_body)

def build_css(css_text, page_size, margin):
    page_css = f"@page {{ size: {page_size}; margin: {margin}; }}"
    return page_css + "\n" + css_text

def write_styled_text(pdf, text):
    if not text:
        return

    parts = re.split(r"(`[^`]+`|\*\*[^*]+\*\*|\*[^*]+\*|\[[^\]]+\]\([^\)]+\))", text)
    for part in parts:
        if not part:
            continue

        if part.startswith("**") and part.endswith("**"):
            pdf.set_font("Helvetica", style="B", size=11)
            try:
                pdf.write(5, part[2:-2])
            except Exception as e:
                if 'Unicode' in str(e) or 'encode' in str(e):
                    safe_part = re.sub(r'[^\x00-\x7F]+', '[?]', part[2:-2])
                    pdf.write(5, safe_part)
                else:
                    raise
            pdf.set_font("Helvetica", size=11)
            continue

        if part.startswith("*") and part.endswith("*"):
            pdf.set_font("Helvetica", style="I", size=11)
            try:
                pdf.write(5, part[1:-1])
            except Exception as e:
                if 'Unicode' in str(e) or 'encode' in str(e):
                    safe_part = re.sub(r'[^\x00-\x7F]+', '[?]', part[1:-1])
                    pdf.write(5, safe_part)
                else:
                    raise
            pdf.set_font("Helvetica", size=11)
            continue

        if part.startswith("`") and part.endswith("`"):
            pdf.set_font("Courier", size=9)
            try:
                pdf.write(5, part[1:-1])
            except Exception as e:
                if 'Unicode' in str(e) or 'encode' in str(e):
                    safe_part = re.sub(r'[^\x00-\x7F]+', '[?]', part[1:-1])
                    pdf.write(5, safe_part)
                else:
                    raise
            pdf.set_font("Helvetica", size=11)
            continue

        link_match = re.match(r"^\[([^\]]+)\]\(([^\)]+)\)$", part)
        if link_match:
            pdf.set_text_color(0, 0, 255)
            pdf.set_font("Helvetica", style="U", size=11)
            try:
                pdf.write(5, link_match.group(1))
            except Exception as e:
                if 'Unicode' in str(e) or 'encode' in str(e):
                    safe_part = re.sub(r'[^\x00-\x7F]+', '[?]', link_match.group(1))
                    pdf.write(5, safe_part)
                else:
                    raise
            pdf.set_font("Helvetica", size=11)
            pdf.set_text_color(0, 0, 0)
            try:
                pdf.write(5, f" ({link_match.group(2)})")
            except Exception as e:
                if 'Unicode' in str(e) or 'encode' in str(e):
                    safe_part = re.sub(r'[^\x00-\x7F]+', '[?]', f" ({link_match.group(2)})")
                    pdf.write(5, safe_part)
                else:
                    raise
            continue

        try:
            pdf.write(5, part)
        except Exception as e:
            if 'Unicode' in str(e) or 'encode' in str(e):
                # Replace unsupported Unicode characters with placeholders
                safe_part = re.sub(r'[^\x00-\x7F]+', '[?]', part)
                pdf.write(5, safe_part)
            else:
                raise

def _safe_write(pdf, h, text):
    """Write text with automatic Unicode fallback."""
    try:
        pdf.write(h, text)
    except Exception as e:
        if 'Unicode' in str(e) or 'encode' in str(e):
            pdf.write(h, re.sub(r'[^\x00-\x7F]+', '?', text))
        else:
            raise


def _safe_cell(pdf, w, h, text, **kwargs):
    """Cell with automatic Unicode fallback."""
    try:
        pdf.cell(w, h, text, **kwargs)
    except Exception as e:
        if 'Unicode' in str(e) or 'encode' in str(e):
            pdf.cell(w, h, re.sub(r'[^\x00-\x7F]+', '?', text), **kwargs)
        else:
            raise


def _strip_inline_md(text):
    """Strip bold/italic markers for measuring, keep plain text."""
    text = re.sub(r'\*\*([^*]+)\*\*', r'\1', text)
    text = re.sub(r'\*([^*]+)\*', r'\1', text)
    text = re.sub(r'`([^`]+)`', r'\1', text)
    text = re.sub(r'\[([^\]]+)\]\([^\)]+\)', r'\1', text)
    return text.strip()


def render_table(pdf, rows):
    """Render a collected set of markdown table rows as a formatted PDF table."""
    if len(rows) < 2:
        return

    header_cells = [c.strip() for c in rows[0].strip('|').split('|')]
    col_count = len(header_cells)

    data_rows = []
    for row_line in rows[1:]:
        stripped = row_line.strip('|').strip()
        if re.match(r'^[\s|:\-]+$', stripped):
            continue
        cells = [c.strip() for c in row_line.strip('|').split('|')]
        while len(cells) < col_count:
            cells.append('')
        data_rows.append(cells[:col_count])

    if not data_rows:
        return

    usable_w = pdf.w - pdf.l_margin - pdf.r_margin
    pdf.set_font("Helvetica", size=9)

    col_max = [0.0] * col_count
    for cells in [header_cells] + data_rows:
        for i, cell in enumerate(cells):
            plain = _strip_inline_md(cell)
            w = pdf.get_string_width(plain) + 6
            if w > col_max[i]:
                col_max[i] = w

    total = sum(col_max)
    if total > usable_w:
        col_widths = [usable_w * (m / total) for m in col_max]
    else:
        col_widths = list(col_max)

    row_h = 7

    if pdf.get_y() + row_h * (len(data_rows) + 1) > pdf.h - pdf.b_margin:
        pdf.add_page()

    pdf.set_font("Helvetica", style="B", size=9)
    pdf.set_fill_color(240, 240, 240)
    for i, cell in enumerate(header_cells):
        plain = _strip_inline_md(cell)
        _safe_cell(pdf, col_widths[i], row_h, plain, border=1, fill=True)
    pdf.ln(row_h)

    pdf.set_font("Helvetica", size=9)
    pdf.set_fill_color(255, 255, 255)
    for row_idx, cells in enumerate(data_rows):
        if pdf.get_y() + row_h > pdf.h - pdf.b_margin:
            pdf.add_page()
            pdf.set_font("Helvetica", style="B", size=9)
            pdf.set_fill_color(240, 240, 240)
            for i, cell in enumerate(header_cells):
                plain = _strip_inline_md(cell)
                _safe_cell(pdf, col_widths[i], row_h, plain, border=1, fill=True)
            pdf.ln(row_h)
            pdf.set_font("Helvetica", size=9)
            pdf.set_fill_color(255, 255, 255)

        stripe = row_idx % 2 == 1
        if stripe:
            pdf.set_fill_color(248, 248, 248)

        for i, cell in enumerate(cells):
            plain = _strip_inline_md(cell)
            _safe_cell(pdf, col_widths[i], row_h, plain, border=1, fill=stripe)

        if stripe:
            pdf.set_fill_color(255, 255, 255)
        pdf.ln(row_h)

    pdf.ln(3)


def render_markdown_to_pdf(pdf, markdown_text):
    in_code_block = False
    table_buffer = []

    for line in markdown_text.splitlines():
        is_table_line = bool(re.match(r'^\s*\|', line))

        if table_buffer and not is_table_line:
            render_table(pdf, table_buffer)
            table_buffer = []

        if is_table_line:
            table_buffer.append(line)
            continue

        if line.startswith("```"):
            in_code_block = not in_code_block
            if in_code_block:
                pdf.ln(2)
                pdf.set_fill_color(244, 244, 244)
            else:
                pdf.ln(2)
            continue

        if in_code_block:
            pdf.set_font("Courier", size=9)
            pdf.set_fill_color(244, 244, 244)
            x = pdf.get_x()
            pdf.set_x(pdf.l_margin)
            _safe_cell(pdf, pdf.w - pdf.l_margin - pdf.r_margin, 5, "  " + line, fill=True)
            pdf.ln(5)
            continue

        if not line.strip():
            pdf.ln(3)
            continue

        if re.match(r'^-{3,}$|^\*{3,}$|^_{3,}$', line.strip()):
            y = pdf.get_y() + 3
            pdf.set_draw_color(200, 200, 200)
            pdf.line(pdf.l_margin, y, pdf.w - pdf.r_margin, y)
            pdf.set_y(y + 4)
            pdf.set_draw_color(0, 0, 0)
            continue

        blockquote = re.match(r"^>\s+(.*)", line)
        if blockquote:
            y_start = pdf.get_y()
            pdf.set_font("Helvetica", style="I", size=10)
            pdf.set_text_color(71, 85, 105)
            pdf.set_x(pdf.l_margin + 8)
            write_styled_text(pdf, blockquote.group(1).strip())
            y_end = pdf.get_y() + 5
            pdf.set_draw_color(203, 213, 225)
            pdf.set_line_width(0.8)
            pdf.line(pdf.l_margin + 3, y_start, pdf.l_margin + 3, y_end)
            pdf.set_line_width(0.2)
            pdf.set_draw_color(0, 0, 0)
            pdf.set_text_color(0, 0, 0)
            pdf.set_x(pdf.l_margin)
            pdf.ln(6)
            pdf.set_font("Helvetica", size=11)
            continue

        heading = re.match(r"^(#{1,6})\s+(.*)", line)
        if heading:
            level = len(heading.group(1))
            size = max(20 - (level - 1) * 2, 11)
            pdf.ln(4 if level <= 2 else 2)
            pdf.set_font("Helvetica", style="B", size=size)
            pdf.set_text_color(17, 24, 39)
            _safe_cell(pdf, 0, size * 0.6, heading.group(2).strip(), new_x="LMARGIN", new_y="NEXT")
            pdf.set_text_color(0, 0, 0)
            if level <= 2:
                y = pdf.get_y() + 1
                pdf.set_draw_color(229, 231, 235)
                pdf.line(pdf.l_margin, y, pdf.w - pdf.r_margin, y)
                pdf.set_draw_color(0, 0, 0)
                pdf.set_y(y + 2)
            pdf.ln(2)
            pdf.set_font("Helvetica", size=11)
            continue

        numbered = re.match(r'^(\d+)\.\s+(.*)', line)
        if numbered:
            pdf.set_font("Helvetica", size=11)
            _safe_cell(pdf, 8, 6, f"{numbered.group(1)}.")
            write_styled_text(pdf, numbered.group(2).strip())
            pdf.ln(6)
            continue

        list_item = re.match(r"^([-*+])\s+(.*)", line)
        if list_item:
            pdf.set_font("Helvetica", size=11)
            pdf.set_text_color(100, 100, 100)
            _safe_cell(pdf, 6, 6, chr(8226))
            pdf.set_text_color(0, 0, 0)
            write_styled_text(pdf, list_item.group(2).strip())
            pdf.ln(6)
            continue

        pdf.set_font("Helvetica", size=11)
        write_styled_text(pdf, line)
        pdf.ln(6)

    if table_buffer:
        render_table(pdf, table_buffer)

def write_pdf(content, backend_name, backend_module, page_size="A4", margin="1in", title="Markdown Document"):
    if backend_name == "weasyprint":
        css_text = build_css(DEFAULT_CSS, page_size, margin)
        html = render_html(content, css_text, title)
        return backend_module(string=html).write_pdf()

    if backend_name == "fpdf":
        margin_mm = parse_margin(margin)
        pdf = backend_module(format=page_size)
        pdf.set_title(title)
        pdf.set_margins(margin_mm, margin_mm, margin_mm)
        pdf.set_auto_page_break(auto=True, margin=margin_mm)
        pdf.add_page()
        render_markdown_to_pdf(pdf, content)

        result = pdf.output()
        if isinstance(result, (bytes, bytearray)):
            return bytes(result)
        return result.encode("latin-1")

    raise RuntimeError(f"Unsupported backend: {backend_name}")

def convert_markdown_to_pdf(markdown_text, page_size='A4', margin='1in'):
    backend_name, backend_module = load_backend("auto")
    return write_pdf(markdown_text, backend_name, backend_module, page_size=page_size, margin=margin)

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