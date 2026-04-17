# Inkdown

> Beautiful PDFs from Markdown. Free, fast, and open source.

Write in Markdown with a live side-by-side preview, then export pixel-perfect PDFs in one click. Built with Next.js, TypeScript, and Tailwind CSS.

## Features

- **Live Preview** — See your formatted document in real-time as you type
- **PDF Export** — Convert to PDF with configurable page size and margins
- **Templates** — 6 professional templates (Resume, README, Meeting Notes, Blog Post, Technical Spec)
- **Dark / Light Mode** — Full theme support with system detection
- **Auto-save** — Content persists to localStorage automatically
- **Drag & Drop** — Import `.md`, `.markdown`, or `.txt` files by dropping them onto the editor
- **Keyboard Shortcuts** — `Ctrl+Shift+E` to export, `Ctrl+S` confirmation
- **Responsive** — Mobile-friendly with tab-based editor/preview switching
- **Undo on Template Load** — Toast with one-click undo when switching templates

## Tech Stack

| Layer | Technology |
|-------|-----------|
| Framework | [Next.js 14](https://nextjs.org) (App Router) |
| Language | [TypeScript](https://typescriptlang.org) |
| Styling | [Tailwind CSS 3](https://tailwindcss.com) + CSS variables |
| UI Primitives | [Radix UI](https://radix-ui.com) (Dialog, Dropdown Menu) |
| Icons | [Lucide React](https://lucide.dev) |
| Preview | [react-markdown](https://github.com/remarkjs/react-markdown) + [remark-gfm](https://github.com/remarkjs/remark-gfm) |
| Toasts | [Sonner](https://sonner.emilkowal.dev) |
| Theming | [next-themes](https://github.com/pacocoursey/next-themes) |
| PDF Backend | Python ([WeasyPrint](https://weasyprint.org) / [fpdf2](https://py-pdf.github.io/fpdf2/)) |
| Hosting | [Vercel](https://vercel.com) (Next.js + Python serverless) |

## Project Structure

```
src/
├── app/
│   ├── layout.tsx          # Root layout with fonts, theme provider, toaster
│   ├── page.tsx            # Entry point — renders EditorWorkspace
│   ├── error.tsx           # Error boundary with retry
│   └── globals.css         # Tailwind + CSS variable theme
├── components/
│   ├── editor-workspace.tsx # Main orchestrator (state, shortcuts, auto-save)
│   ├── navbar.tsx          # Top bar — logo, templates dropdown, export button
│   ├── editor.tsx          # Split-pane editor with drag-and-drop
│   ├── preview.tsx         # Live markdown preview (react-markdown)
│   ├── export-dialog.tsx   # PDF export settings modal
│   └── theme-toggle.tsx    # Dark/light mode toggle
├── lib/
│   ├── utils.ts            # cn() class merging utility
│   └── templates.ts        # 6 professional markdown templates
└── providers/
    └── theme-provider.tsx  # next-themes wrapper
api/
└── convert.py              # Vercel Python serverless — markdown → PDF
```

## Getting Started

### Prerequisites

- **Node.js** 18+
- **Python** 3.9+ (for PDF conversion)
- [WeasyPrint system dependencies](https://doc.courtbouillon.org/weasyprint/stable/first_steps.html#installation) (or the pure-Python `fpdf2` fallback)

### Install

```bash
# JavaScript dependencies
npm install

# Python dependencies
pip install -r requirements.txt
```

### Development

```bash
npm run dev
```

Open [http://localhost:3000](http://localhost:3000). The editor and preview work locally; PDF export requires [Vercel CLI](https://vercel.com/docs/cli) (`vercel dev`) to serve the Python function.

### Production Build

```bash
npm run build
npm start
```

## Deployment

**Live at [inkdown.intelliforge.tech](https://inkdown.intelliforge.tech)**

Deployed on Vercel with dual builders (Next.js + Python serverless):

```bash
npm install -g vercel
vercel --prod
```

The `vercel.json` configures `/api/convert` to route to the Python handler.

## CLI Usage

A standalone CLI is also available for local conversion:

```bash
# Basic conversion
python md2pdf.py input.md

# Custom output, page size, and margins
python md2pdf.py input.md output.pdf --page-size Letter --margin 0.75in

# With custom CSS (WeasyPrint backend only)
python md2pdf.py input.md output.pdf --css styles.css

# Pipe from stdin
cat input.md | python md2pdf.py - output.pdf
```

## Testing

```bash
# Python unit tests
python -m unittest tests/test_md2pdf.py

# E2E tests (Playwright)
npm run test:e2e
```

## License

MIT
