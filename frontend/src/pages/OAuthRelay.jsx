import React, { useEffect, useState } from 'react'
import { useNavigate } from 'react-router-dom'

export default function OAuthRelay() {
  const navigate = useNavigate()
  const [error, setError] = useState(null)

  useEffect(() => {
    const sendToBackend = async () => {
      try {
        // Post the full URL (including code & state) back to the backend to complete OAuth
        let apiBase = import.meta.env.VITE_API_BASE
        if (!apiBase) {
          const origin = `${window.location.protocol}//${window.location.hostname}:5000`
          apiBase = origin
        }
        const res = await fetch(`${apiBase}/oauth2callback/complete`, {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          credentials: 'include',
          body: JSON.stringify({ authorization_response: window.location.href })
        })
        if (!res.ok) throw new Error('OAuth completion failed')
        navigate('/dashboard', { replace: true })
      } catch (e) {
        setError(e.message)
        navigate('/', { replace: true })
      }
    }
    sendToBackend()
  }, [navigate])

  return (
    <div className="min-h-screen flex items-center justify-center bg-slate-900 text-white">
      {error ? 'Redirect failed. Returning to home…' : 'Finishing sign-in…'}
    </div>
  )
}


