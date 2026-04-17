#!/usr/bin/env python3
"""Markdown to PDF converter tool."""

import argparse
import io
import os
import re
import sys

try:
    from markdown import markdown
except ImportError:
    print("Error: missing dependency 'markdown'. Install with 'pip install markdown'.")
    sys.exit(1)


def load_backend(backend_preference):
    if backend_preference in ("weasyprint", "auto"):
        try:
            from weasyprint import HTML
            return "weasyprint", HTML
        except (ImportError, OSError) as exc:
            if backend_preference == "weasyprint":
                print("Error: WeasyPrint import failed. Install the Python package and required native libraries.")
                print("Install Python deps with: pip install weasyprint")
                print("On macOS, also install: brew install cairo pango gdk-pixbuf libffi")
                print(f"Details: {exc}")
                sys.exit(1)
            fallback_error = exc
    else:
        fallback_error = None

    if backend_preference in ("fpdf", "auto"):
        try:
            from fpdf import FPDF
            return "fpdf", FPDF
        except ImportError as exc:
            if backend_preference == "fpdf":
                print("Error: missing dependency 'fpdf2'. Install with 'pip install fpdf2'.")
                print(f"Details: {exc}")
                sys.exit(1)
            fallback_error = exc

    print("Error: could not load a PDF backend.")
    if 'fallback_error' in locals():
        print(f"First backend error: {fallback_error}")
    sys.exit(1)

DEFAULT_CSS = """
body {
    font-family: Arial, Helvetica, sans-serif;
    line-height: 1.5;
    margin: 1.25in;
    color: #202124;
}
code, pre {
    font-family: Menlo, Monaco, Consolas, 'Courier New', monospace;
}
pre {
    background: #f4f4f4;
    padding: 0.75rem;
    overflow-x: auto;
}
img {
    max-width: 100%;
}
h1, h2, h3, h4, h5, h6 {
    color: #111827;
}
blockquote {
    border-left: 4px solid #cbd5e1;
    margin: 1.5em 0;
    padding-left: 1em;
    color: #475569;
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


def parse_args():
    parser = argparse.ArgumentParser(description="Convert Markdown files to PDF.")
    parser.add_argument("input", nargs="?", default="-", help="Path to the Markdown input file, or '-' to read from stdin.")
    parser.add_argument("output", nargs="?", help="Path to the PDF output file, or '-' to write to stdout. Defaults to the input name with .pdf.")
    parser.add_argument("--css", help="Optional CSS file to style the generated PDF.")
    parser.add_argument("--title", default="Markdown Document", help="Title used in the generated PDF document.")
    parser.add_argument("--page-size", default="A4", help="Page size for PDF output (A4, Letter, etc.).")
    parser.add_argument("--margin", default="1in", help="Page margin for PDF output.")
    parser.add_argument("--backend", choices=["auto", "weasyprint", "fpdf"], default="auto", help="PDF generation backend to use.")
    parser.add_argument("--verbose", action="store_true", help="Show extra status messages.")
    return parser.parse_args()


def load_file(path):
    with open(path, "r", encoding="utf-8") as handle:
        return handle.read()


def render_html(markdown_text, css_text, title):
    html_body = markdown(markdown_text, extensions=["extra", "fenced_code", "tables", "toc"])
    return HTML_TMPL.format(title=title, css=css_text, body=html_body)


def build_css(css_text, page_size, margin):
    page_css = f"@page {{ size: {page_size}; margin: {margin}; }}"
    return page_css + "\n" + css_text


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


def render_markdown_to_pdf(pdf, markdown_text):
    in_code_block = False
    for line in markdown_text.splitlines():
        if line.startswith("```"):
            in_code_block = not in_code_block
            pdf.ln(4)
            continue

        if in_code_block:
            pdf.set_font("Courier", size=9)
            pdf.multi_cell(0, 5, line)
            continue

        if not line.strip():
            pdf.ln(4)
            continue

        blockquote = re.match(r"^>\s+(.*)", line)
        if blockquote:
            pdf.set_font("Helvetica", style="I", size=11)
            pdf.set_x(pdf.l_margin + 5)
            pdf.multi_cell(0, 6, blockquote.group(1).strip())
            pdf.set_x(pdf.l_margin)
            pdf.ln(1)
            pdf.set_font("Helvetica", size=11)
            continue

        heading = re.match(r"^(#{1,6})\s+(.*)", line)
        if heading:
            size = max(18 - (len(heading.group(1)) - 1) * 2, 12)
            pdf.set_font("Helvetica", style="B", size=size)
            pdf.cell(0, 6, heading.group(2).strip(), new_x="LMARGIN", new_y="NEXT")
            pdf.ln(2)
            pdf.set_font("Helvetica", size=11)
            continue

        list_item = re.match(r"^([-*+])\s+(.*)", line)
        if list_item:
            pdf.set_font("Helvetica", size=11)
            pdf.cell(4, 6, "-")
            write_styled_text(pdf, list_item.group(2).strip())
            pdf.ln(6)
            continue

        pdf.set_font("Helvetica", size=11)
        write_styled_text(pdf, line)
        pdf.ln(6)


def write_pdf(content, output_path, backend_name, backend_module, page_size, margin, title):
    if backend_name == "weasyprint":
        html = content
        if output_path == "-":
            return backend_module(string=html).write_pdf()
        backend_module(string=html).write_pdf(output_path)
        return None

    if backend_name == "fpdf":
        margin_mm = parse_margin(margin)
        pdf = backend_module(format=page_size)
        pdf.set_title(title)
        pdf.set_margins(margin_mm, margin_mm, margin_mm)
        pdf.set_auto_page_break(auto=True, margin=margin_mm)
        pdf.add_page()
        render_markdown_to_pdf(pdf, content)

        if output_path == "-":
            result = pdf.output()
            if isinstance(result, (bytes, bytearray)):
                return bytes(result)
            return result.encode("latin-1")
        pdf.output(output_path)
        return None

    raise RuntimeError(f"Unsupported backend: {backend_name}")


def main():
    args = parse_args()
    backend_name, backend_module = load_backend(args.backend)

    if args.input == "-":
        markdown_text = sys.stdin.read()
        input_label = "stdin"
        output_path = args.output if args.output is not None else "-"
    else:
        input_path = os.path.abspath(args.input)
        if not os.path.isfile(input_path):
            print(f"Error: markdown file not found: {input_path}")
            sys.exit(1)

        markdown_text = load_file(input_path)
        input_label = input_path
        output_path = args.output
        if output_path is None:
            base, _ = os.path.splitext(input_path)
            output_path = f"{base}.pdf"

    if output_path != "-":
        output_path = os.path.abspath(output_path)

    css_text = DEFAULT_CSS
    if args.css:
        css_path = os.path.abspath(args.css)
        if not os.path.isfile(css_path):
            print(f"Error: css file not found: {css_path}")
            sys.exit(1)
        css_text = load_file(css_path)

    if backend_name == "weasyprint":
        css_text = build_css(css_text, args.page_size, args.margin)
        html = render_html(markdown_text, css_text, args.title)
        pdf_bytes = write_pdf(html, output_path, backend_name, backend_module, args.page_size, args.margin, args.title)
    else:
        pdf_bytes = write_pdf(markdown_text, output_path, backend_name, backend_module, args.page_size, args.margin, args.title)

    if output_path == "-":
        sys.stdout.buffer.write(pdf_bytes)
        if args.verbose:
            print("Converted markdown from stdin to PDF on stdout.", file=sys.stderr)
    else:
        if args.verbose:
            print(f"Converted '{input_label}' to '{output_path}'", file=sys.stderr)
        else:
            print(f"Converted '{input_label}' to '{output_path}'")


if __name__ == "__main__":
    main()
