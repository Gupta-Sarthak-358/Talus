import React from 'react';

/** Prevents a single render error from blanking the entire app. */
export default class ErrorBoundary extends React.Component {
  constructor(props) {
    super(props);
    this.state = { error: null };
  }

  static getDerivedStateFromError(error) {
    return { error };
  }

  componentDidCatch(error, info) {
    // Surface in console so the Vite terminal/browser console shows the cause
    console.error('TALUS UI crashed:', error, info?.componentStack);
  }

  render() {
    if (this.state.error) {
      let lang = 'en';
      try { lang = localStorage.getItem('talus_lang') || 'en'; } catch { /* default */ }
      const copy = {
        hi: { title: 'TALUS UI त्रुटि', retry: 'पुनः प्रयास' },
        ne: { title: 'TALUS UI त्रुटि', retry: 'पुन: प्रयास' },
      }[lang] || { title: 'TALUS UI error', retry: 'Retry' };
      const stack = String(this.state.error?.stack || '').slice(0, 800);
      return (
        <div style={{ padding: 32, fontFamily: 'monospace', color: '#f87171', maxWidth: 720, margin: '0 auto' }}>
          <h2 style={{ marginBottom: 8 }}>{copy.title}</h2>
          <p style={{ fontSize: 12, color: '#94a3b8', marginBottom: 12 }}>A component crashed. This is usually a missing array (zones/roads/reports) while data loads or backend is offline. Retry will remount.</p>
          <pre style={{ whiteSpace: 'pre-wrap', fontSize: 12, color: '#e2e8f0', background: '#0f172a', padding: 12, borderRadius: 8, overflow: 'auto' }}>
            {String(this.state.error?.message || this.state.error)}
            {stack ? `\n\n${stack}` : ''}
          </pre>
          <div style={{ display: 'flex', gap: 8, marginTop: 16 }}>
            <button
              onClick={() => { this.setState({ error: null }); window.location.reload(); }}
              style={{ padding: '8px 16px', background: '#334155', color: 'white', border: 'none', borderRadius: 8, cursor: 'pointer' }}
            >
              {copy.retry} + Reload
            </button>
            <button
              onClick={() => this.setState({ error: null })}
              style={{ padding: '8px 16px', background: '#1e293b', color: '#cbd5e1', border: '1px solid #334155', borderRadius: 8, cursor: 'pointer' }}
            >
              Dismiss
            </button>
          </div>
        </div>
      );
    }
    return this.props.children;
  }
}