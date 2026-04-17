import { useState } from 'react';
import Head from 'next/head';
import fs from 'fs';
import path from 'path';

export async function getStaticProps() {
  const filePath = path.join(process.cwd(), 'test.md');
  const initialMarkdown = fs.readFileSync(filePath, 'utf8');
  return {
    props: {
      initialMarkdown,
    },
  };
}

export default function Home({ initialMarkdown }) {
  const [markdown, setMarkdown] = useState(initialMarkdown);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');

  const handleConvert = async () => {
    if (!markdown.trim()) {
      setError('Please enter some Markdown content.');
      return;
    }

    setLoading(true);
    setError('');

    try {
      const response = await fetch('/api/convert', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ markdown }),
      });

      if (!response.ok) {
        throw new Error('Conversion failed');
      }

      const blob = await response.blob();
      const url = window.URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = 'shreya_resume.pdf';
      document.body.appendChild(a);
      a.click();
      window.URL.revokeObjectURL(url);
      document.body.removeChild(a);
    } catch (err) {
      setError('Failed to convert Markdown to PDF. Please try again.');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="container">
      <Head>
        <title>Shreya R | AI-Powered Portfolio & Resume</title>
        <meta name="description" content="Portfolio of Shreya R, Software Engineering Evaluator. Convert My Resume to PDF instantly." />
      </Head>

      <style jsx global>{`
        :root {
          --primary: #6366f1;
          --primary-hover: #4f46e5;
          --bg-gradient: linear-gradient(135deg, #0f172a 0%, #1e1b4b 100%);
          --card-bg: rgba(255, 255, 255, 0.05);
          --card-border: rgba(255, 255, 255, 0.1);
          --text-main: #f8fafc;
          --text-muted: #94a3b8;
        }

        body {
          margin: 0;
          padding: 0;
          font-family: 'Inter', -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
          background: var(--bg-gradient);
          color: var(--text-main);
          min-height: 100vh;
        }

        .container {
          max-width: 1000px;
          margin: 0 auto;
          padding: 40px 20px;
        }

        header {
          text-align: center;
          margin-bottom: 50px;
          animation: fadeInDown 0.8s ease-out;
        }

        h1 {
          font-size: 3rem;
          font-weight: 800;
          margin-bottom: 10px;
          background: linear-gradient(to right, #818cf8, #c084fc);
          -webkit-background-clip: text;
          -webkit-text-fill-color: transparent;
        }

        .subtitle {
          color: var(--text-muted);
          font-size: 1.1rem;
        }

        .main-card {
          background: var(--card-bg);
          backdrop-filter: blur(12px);
          border: 1px solid var(--card-border);
          border-radius: 24px;
          padding: 30px;
          box-shadow: 0 25px 50px -12px rgba(0, 0, 0, 0.5);
          animation: fadeInUp 1s ease-out;
        }

        .editor-header {
          display: flex;
          justify-content: space-between;
          align-items: center;
          margin-bottom: 20px;
        }

        h2 {
          font-size: 1.5rem;
          margin: 0;
        }

        textarea {
          width: 100%;
          min-height: 500px;
          background: rgba(0, 0, 0, 0.3);
          border: 1px solid var(--card-border);
          border-radius: 12px;
          padding: 20px;
          color: #e2e8f0;
          font-family: 'Fira Code', 'Monaco', monospace;
          font-size: 14px;
          line-height: 1.6;
          resize: vertical;
          margin-bottom: 25px;
          transition: border-color 0.3s ease;
        }

        textarea:focus {
          outline: none;
          border-color: var(--primary);
        }

        .controls {
          display: flex;
          flex-direction: column;
          align-items: center;
          gap: 15px;
        }

        .convert-btn {
          background: var(--primary);
          color: white;
          border: none;
          padding: 16px 40px;
          border-radius: 14px;
          font-size: 1.1rem;
          font-weight: 600;
          cursor: pointer;
          transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
          box-shadow: 0 10px 15px -3px rgba(99, 102, 241, 0.4);
        }

        .convert-btn:hover:not(:disabled) {
          background: var(--primary-hover);
          transform: translateY(-2px);
          box-shadow: 0 20px 25px -5px rgba(99, 102, 241, 0.5);
        }

        .convert-btn:disabled {
          opacity: 0.6;
          cursor: not-allowed;
        }

        .error-msg {
          color: #f87171;
          font-size: 0.9rem;
        }

        .features {
          margin-top: 60px;
          display: grid;
          grid-template-columns: repeat(auto-fit, minmax(280px, 1fr));
          gap: 25px;
        }

        .feature-item {
          background: rgba(255, 255, 255, 0.03);
          padding: 25px;
          border-radius: 18px;
          border: 1px solid var(--card-border);
        }

        .feature-item h3 {
          margin-top: 0;
          color: #818cf8;
        }

        @keyframes fadeInDown {
          from { opacity: 0; transform: translateY(-20px); }
          to { opacity: 1; transform: translateY(0); }
        }

        @keyframes fadeInUp {
          from { opacity: 0; transform: translateY(20px); }
          to { opacity: 1; transform: translateY(0); }
        }

        @media (max-width: 640px) {
          h1 { font-size: 2.2rem; }
          .container { padding: 20px; }
        }
      `}</style>

      <header>
        <h1>Shreya R</h1>
        <p className="subtitle">AI-Powered Markdown to PDF Portfolio</p>
      </header>

      <main className="main-card">
        <div className="editor-header">
          <h2>Resume Editor</h2>
          <span style={{ fontSize: '0.8rem', color: 'var(--text-muted)' }}>Auto-aligned with latest resume</span>
        </div>

        <textarea
          value={markdown}
          onChange={(e) => setMarkdown(e.target.value)}
          placeholder="Enter Markdown content..."
        />

        <div className="controls">
          <button
            className="convert-btn"
            onClick={handleConvert}
            disabled={loading}
          >
            {loading ? 'Processing...' : 'Export Resume to PDF'}
          </button>
          {error && <p className="error-msg">{error}</p>}
        </div>
      </main>

      <section className="features">
        <div className="feature-item">
          <h3>Professional Proofing</h3>
          <p>Instantly transform your aligned resume into a production-grade PDF document with standardized margins and typography.</p>
        </div>
        <div className="feature-item">
          <h3>AI-Aligned Content</h3>
          <p>Optimized for Software Engineering Evaluator roles, emphasizing metrics, technical depth, and AI evaluation expertise.</p>
        </div>
        <div className="feature-item">
          <h3>Vercel Powered</h3>
          <p>State-of-the-art serverless architecture ensures fast conversion and globally distributed access to your professional credentials.</p>
        </div>
      </section>
      
      <footer style={{ marginTop: '60px', textAlign: 'center', color: 'var(--text-muted)', fontSize: '0.9rem' }}>
        &copy; {new Date().getFullYear()} Shreya R. Built with Next.js & Python.
      </footer>
    </div>
  );
}