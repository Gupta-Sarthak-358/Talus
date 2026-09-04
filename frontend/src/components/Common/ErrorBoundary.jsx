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
      // Class component: read persisted language directly (no hooks)
      let lang = 'en';
      try { lang = localStorage.getItem('talus_lang') || 'en'; } catch { /* default */ }
      const copy = {
        hi: { title: 'TALUS UI त्रुटि', retry: 'पुनः प्रयास' },
        ne: { title: 'TALUS UI त्रुटि', retry: 'पुन: प्रयास' },
      }[lang] || { title: 'TALUS UI error', retry: 'Retry' };
      return (
        <div style={{ padding: 32, fontFamily: 'monospace', color: '#f87171' }}>
          <h2 style={{ marginBottom: 12 }}>{copy.title}</h2>
          <pre style={{ whiteSpace: 'pre-wrap', fontSize: 12, color: '#cbd5e1' }}>
            {String(this.state.error?.message || this.state.error)}
          </pre>
          <button
            onClick={() => this.setState({ error: null })}
            style={{ marginTop: 16, padding: '8px 16px', background: '#334155',
                     color: 'white', border: 'none', borderRadius: 8, cursor: 'pointer' }}
          >
            {copy.retry}
          </button>
        </div>
      );
    }
    return this.props.children;
  }
}