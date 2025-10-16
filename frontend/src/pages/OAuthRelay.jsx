import React, { useEffect, useState } from 'react'
import { useNavigate } from 'react-router-dom'

export default function OAuthRelay() {
  const navigate = useNavigate()
  const [error, setError] = useState(null)

  useEffect(() => {
    const sendToBackend = async () => {
      try {
        const backendUrl = import.meta.env.VITE_BACKEND_URL
        if (!backendUrl) {
          throw new Error('Backend URL not configured')
        }

        // Get the authorization code from URL
        const params = new URLSearchParams(window.location.search)
        const code = params.get('code')
        if (!code) {
          throw new Error('No authorization code received')
        }

        const res = await fetch(`${backendUrl}/oauth2callback/complete`, {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          credentials: 'include',
          body: JSON.stringify({ 
            authorization_response: window.location.href,
            code: code
          })
        })

        if (!res.ok) {
          const data = await res.json().catch(() => ({}))
          throw new Error(data?.error || 'OAuth completion failed')
        }

        // On success, redirect to dashboard
        navigate('/dashboard', { replace: true })
      } catch (e) {
        console.error('OAuth error:', e)
        setError(e.message)
        // Wait a moment before redirecting to show the error
        setTimeout(() => {
          navigate('/', { replace: true })
        }, 3000)
      }
    }
    sendToBackend()
  }, [navigate])

  return (
    <div className="min-h-screen flex items-center justify-center bg-gradient-to-br from-slate-950 via-slate-900 to-slate-800 text-white">
      <div className="bg-slate-900/70 backdrop-blur-xl border border-slate-700 rounded-xl p-6 text-center">
        {error ? (
          <div className="text-red-400">
            <div className="font-semibold mb-2">Authentication Failed</div>
            <div className="text-sm">{error}</div>
            <div className="text-slate-400 text-sm mt-2">Returning to home...</div>
          </div>
        ) : (
          <div className="flex items-center gap-3">
            <svg className="animate-spin h-5 w-5 text-cyan-400" viewBox="0 0 24 24">
              <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"/>
              <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8v4a4 4 0 00-4 4H4z"/>
            </svg>
            <span>Finishing sign-in...</span>
          </div>
        )}
      </div>
    </div>
  )
}