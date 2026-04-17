# Markdown to PDF Converter

A simple Python tool to convert Markdown files into PDF documents, now with a web interface deployable to Vercel.

## Setup

Install the Python dependencies:

```bash
pip install -r requirements.txt
```

> Note: `WeasyPrint` may require additional system libraries on macOS. If you hit install errors, install `cairo`, `pango`, and `gdk-pixbuf` with Homebrew:

```bash
brew install cairo pango gdk-pixbuf libffi
```

## Usage

### Local Development

```bash
npm install
npm run dev
```

Open [http://localhost:3000](http://localhost:3000) in your browser.

### CLI Usage

```bash
python md2pdf.py input.md
```

This will generate `input.pdf` next to your Markdown file.

### Custom output path

```bash
python md2pdf.py input.md output.pdf
```

### Optional CSS styling

```bash
python md2pdf.py input.md output.pdf --css styles.css
```

### Page size and margins

```bash
python md2pdf.py input.md output.pdf --page-size Letter --margin 0.75in
```

### Read Markdown from stdin

```bash
cat input.md | python md2pdf.py - output.pdf
```

### Write PDF to stdout

```bash
python md2pdf.py input.md - > output.pdf
```

### Select backend explicitly

```bash
python md2pdf.py input.md output.pdf --backend fpdf
```

The tool tries WeasyPrint first by default, and falls back to the pure-Python `fpdf2` backend if WeasyPrint is unavailable. The `fpdf` backend supports headings, lists, blockquotes, bold, italic, and inline code formatting.

> Note: CSS styling is only applied when using the WeasyPrint backend.

## Testing

Run the built-in unit tests after installing dependencies:

```bash
python -m unittest tests/test_md2pdf.py
```

## Deployment to Vercel

The app is deployed at: https://markdown-to-pdf-converter-taupe.vercel.app

To redeploy after changes:

1. Install Vercel CLI:
   ```bash
   npm install -g vercel
   ```

2. Deploy:
   ```bash
   vercel --prod
   ```

## Example

```bash
python md2pdf.py README.md README.pdf
```
