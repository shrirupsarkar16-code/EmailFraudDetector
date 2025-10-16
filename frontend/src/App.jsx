import React, { useEffect, useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { ShieldCheck } from 'lucide-react'

export default function App() {
  const [emails, setEmails] = useState(null)
  const [error, setError] = useState(null)
  const [loading, setLoading] = useState(false)
  const navigate = useNavigate()

  const handleLogin = () => {
    let apiBase = import.meta.env.VITE_API_BASE;
    if (!apiBase) {
      const origin = `${window.location.protocol}//${window.location.host}`;
      apiBase = (window.location.port === '5000') ? origin : 'http://localhost:5000';
    }
    window.location.href = `${apiBase}/auth`;
  };

  const handleScan = async () => {
    try {
      setLoading(true)
      let apiBase = import.meta.env.VITE_API_BASE;
      if (!apiBase) {
        const origin = `${window.location.protocol}//${window.location.host}`;
        apiBase = (window.location.port === '5000') ? origin : 'http://localhost:5000';
      }
      const res = await fetch(`${apiBase}/api/scan`, { method: 'POST', credentials: 'include' })
      if (!res.ok) {
        const body = await res.json().catch(() => ({}))
        throw new Error(body?.error || `Scan failed (${res.status})`)
      }
      const data = await res.json()
      const list = data.emails || []
      setEmails(list)
      try { sessionStorage.setItem('scan_result', JSON.stringify(list)) } catch {}
      setError(null)
      // Navigate to dashboard after successful scan
      navigate('/dashboard')
    } catch (e) {
      setError(e.message)
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    // If redirected back to backend origin after OAuth, trigger scan automatically
    if (window.location.port === '5000') {
      handleScan().catch(() => {})
    }
  }, [])

  const stats = React.useMemo(() => {
    if (!emails) return null
    const total = emails.length
    const spam = emails.filter(e => e.prediction?.label === 'spam').length
    const suspiciousLinks = emails.reduce((acc, e) => acc + (e.link_count || 0), 0)
    const fraud = spam // alias for clarity
    const fraudList = emails.filter(e => e.prediction?.label === 'spam')
    return { total, suspiciousLinks, spam, fraud, fraudList }
  }, [emails])

  return (
    <div className="min-h-screen flex items-center justify-center bg-gradient-to-br from-slate-950 via-slate-900 to-slate-800 text-white p-4">
      <div className="max-w-md w-full bg-slate-900/70 backdrop-blur-xl border border-slate-700 rounded-3xl shadow-2xl p-10 text-center">
        <div className="flex justify-center mb-6">
          <div className="p-4 rounded-2xl bg-cyan-500/10 border border-cyan-500">
            <ShieldCheck size={48} className="text-cyan-400" />
          </div>
        </div>

        <h1 className="text-3xl font-bold text-cyan-400 mb-2">Email Fraud Detector</h1>
        <p className="text-slate-300 mb-8 tracking-wide">AI-powered Gmail security & fraud detection system</p>

        <div className="flex flex-col gap-4">
          <button
            onClick={handleLogin}
            className="w-full py-3 bg-cyan-500 hover:bg-cyan-400 text-slate-950 font-semibold rounded-xl transition-transform transform hover:scale-[1.02] flex items-center justify-center gap-2 shadow-lg"
          >
            <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" className="w-5 h-5">
              <path d="M4 4h16v16H4z" />
              <path d="M22 12l-10 7L2 12" />
            </svg>
            Sign in with Google
          </button>
        </div>

        {error && (
          <div className="mt-4 text-red-400 text-center">{error}</div>
        )}

        {stats && !loading && (
          <div className="mt-8">
            <h2 className="text-xl font-semibold mb-4">Scan summary</h2>
            <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
              <div className="bg-slate-800/60 rounded-xl p-4 border border-slate-700">
                <div className="text-slate-400 text-sm">Total scanned</div>
                <div className="text-2xl font-bold">{stats.total}</div>
              </div>
              <div className="bg-slate-800/60 rounded-xl p-4 border border-slate-700">
                <div className="text-slate-400 text-sm">Suspicious links</div>
                <div className="text-2xl font-bold">{stats.suspiciousLinks}</div>
              </div>
              <div className="bg-slate-800/60 rounded-xl p-4 border border-slate-700">
                <div className="text-slate-400 text-sm">Spam</div>
                <div className="text-2xl font-bold">{stats.spam}</div>
              </div>
              <div className="bg-slate-800/60 rounded-xl p-4 border border-slate-700">
                <div className="text-slate-400 text-sm">Fraud emails</div>
                <div className="text-2xl font-bold">{stats.fraud}</div>
              </div>
            </div>

            <h3 className="text-lg font-semibold mt-8 mb-3">Fraud email list</h3>
            <div className="space-y-3">
              {stats.fraudList.map((e, i) => (
                <div key={e.id || i} className="p-4 bg-slate-800/60 rounded-xl border border-slate-700">
                  <div className="flex justify-between">
                    <div className="font-semibold text-cyan-300">{e.subject || 'No subject'}</div>
                    <div className="text-sm text-red-400">score {(e.prediction?.score ?? 0).toFixed(2)}</div>
                  </div>
                  <div className="text-sm text-slate-400">{e.from}</div>
                  {Array.isArray(e.links) && e.links.length > 0 && (
                    <div className="mt-2 text-sm">
                      <div className="text-slate-400 mb-1">Suspicious links:</div>
                      <ul className="list-disc list-inside space-y-1">
                        {e.links.map((u, idx) => (
                          <li key={idx}>
                            <a className="text-cyan-300 underline break-all" href={u} target="_blank" rel="noreferrer noopener">{u}</a>
                          </li>
                        ))}
                      </ul>
                    </div>
                  )}
                </div>
              ))}
              {stats.fraudList.length === 0 && (
                <div className="text-slate-400">No fraud emails found.</div>
              )}
            </div>
          </div>
        )}

        <div className="mt-8 text-left text-sm text-slate-400 space-y-1">
          <p>✓ Read-only Gmail access</p>
          <p>✓ AI-powered fraud & spam detection</p>
          <p>✓ Your data stays private and secure</p>
        </div>

        <footer className="mt-10 text-xs text-slate-500">
          <p>© 2025 Email Fraud Detector. All rights reserved.</p>
        </footer>
      </div>
    </div>
  );
}

