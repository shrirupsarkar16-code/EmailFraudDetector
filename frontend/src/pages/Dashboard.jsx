import React, { useEffect, useMemo, useState } from 'react'

export default function Dashboard() {
  const [emails, setEmails] = useState([])
  const [error, setError] = useState(null)
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    const doScan = async () => {
      try {
        setLoading(true)
        let apiBase = import.meta.env.VITE_API_BASE
        if (!apiBase) {
          const origin = `${window.location.protocol}//${window.location.host}`
          apiBase = (window.location.port === '5000') ? origin : 'http://localhost:5000'
        }
        const res = await fetch(`${apiBase}/api/scan`, { method: 'POST', credentials: 'include' })
        if (!res.ok) {
          const body = await res.json().catch(() => ({}))
          throw new Error(body?.error || `Scan failed (${res.status})`)
        }
        const data = await res.json()
        const list = data?.emails || []
        setEmails(list)
        try { sessionStorage.setItem('scan_result', JSON.stringify(list)) } catch {}
        setError(null)
      } catch (e) {
        // Fallback to any existing session results if available
        const stored = sessionStorage.getItem('scan_result')
        if (stored) {
          try { setEmails(JSON.parse(stored) || []) } catch {}
        }
        setError(e.message)
      } finally {
        setLoading(false)
      }
    }
    doScan()
  }, [])

  const stats = useMemo(() => {
    const total = emails.length
    const suspiciousEmails = emails.filter(e => (e.link_count || 0) > 0).length
    const suspiciousLinks = emails.reduce((acc, e) => acc + (e.link_count || 0), 0)
    const spam = emails.filter(e => e.prediction?.label === 'spam').length
    return { total, suspiciousEmails, suspiciousLinks, spam }
  }, [emails])

  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-950 via-slate-900 to-slate-800 text-white p-6">
      <div className="max-w-6xl mx-auto">
        <h1 className="text-3xl font-bold text-cyan-400 mb-6">Inbox Security Dashboard</h1>

        {loading && (
          <div className="flex items-center gap-3 text-slate-200 bg-slate-900/70 border border-slate-700 rounded-xl p-4">
            <svg className="animate-spin h-5 w-5 text-cyan-400" viewBox="0 0 24 24"><circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"/><path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8v4a4 4 0 00-4 4H4z"/></svg>
            <span>Scanning emails…</span>
          </div>
        )}

        {error && (
          <div className="mt-4 text-red-400">{error}</div>
        )}

        {!loading && (
          <>
            <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mb-8">
              <div className="bg-slate-900/70 border border-slate-700 rounded-xl p-4">
                <div className="text-slate-400 text-sm">Total emails scanned</div>
                <div className="text-2xl font-bold">{stats.total}</div>
              </div>
              <div className="bg-slate-900/70 border border-slate-700 rounded-xl p-4">
                <div className="text-slate-400 text-sm">Total suspicious emails</div>
                <div className="text-2xl font-bold">{stats.suspiciousEmails}</div>
              </div>
              <div className="bg-slate-900/70 border border-slate-700 rounded-xl p-4">
                <div className="text-slate-400 text-sm">Total suspicious links</div>
                <div className="text-2xl font-bold">{stats.suspiciousLinks}</div>
              </div>
              <div className="bg-slate-900/70 border border-slate-700 rounded-xl p-4">
                <div className="text-slate-400 text-sm">Total spam emails</div>
                <div className="text-2xl font-bold">{stats.spam}</div>
              </div>
            </div>

            <div className="bg-slate-900/70 border border-slate-700 rounded-2xl overflow-hidden">
              <div className="px-6 py-4 border-b border-slate-700 flex items-center justify-between">
                <h2 className="text-lg font-semibold">All emails</h2>
                <div className="text-slate-400 text-sm">Showing {emails.length}</div>
              </div>
              <div className="overflow-x-auto">
                <table className="min-w-full text-sm">
                  <thead className="bg-slate-800/60 text-slate-300">
                    <tr>
                      <th className="text-left px-6 py-3 font-medium">Sender</th>
                      <th className="text-left px-6 py-3 font-medium">Subject</th>
                      <th className="text-left px-6 py-3 font-medium">Suspicious links</th>
                    </tr>
                  </thead>
                  <tbody>
                    {emails.map((e, i) => (
                      <tr key={e.id || i} className="border-t border-slate-800">
                        <td className="px-6 py-3 text-slate-300 whitespace-nowrap">{e.from || 'Unknown'}</td>
                        <td className="px-6 py-3 text-slate-200">
                          <div className="line-clamp-2 max-w-xl">{e.subject || 'No subject'}</div>
                        </td>
                        <td className="px-6 py-3">
                          {Array.isArray(e.links) && e.links.length > 0 ? (
                            <div className="space-y-1">
                              {e.links.slice(0, 3).map((u, idx) => (
                                <div key={idx} className="truncate max-w-md">
                                  <a className="text-cyan-300 underline" href={u} target="_blank" rel="noreferrer noopener">{u}</a>
                                </div>
                              ))}
                              {e.links.length > 3 && (
                                <div className="text-slate-400 text-xs">+{e.links.length - 3} more</div>
                              )}
                            </div>
                          ) : (
                            <span className="text-slate-500">None</span>
                          )}
                        </td>
                      </tr>
                    ))}
                    {emails.length === 0 && (
                      <tr>
                        <td className="px-6 py-6 text-slate-400" colSpan={3}>No emails available.</td>
                      </tr>
                    )}
                  </tbody>
                </table>
              </div>
            </div>
          </>
        )}
      </div>
    </div>
  )
}


