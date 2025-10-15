import React from 'react'
import { ShieldCheck } from 'lucide-react'

export default function App() {
  const handleLogin = () => {
    // Use production URL in production, fallback to localhost for development
    const apiUrl = import.meta.env.PROD 
      ? 'https://email-scam-detector-api.onrender.com/auth'
      : 'http://localhost:5000/auth';
    window.location.href = apiUrl;
  };

  return (
    <div className="min-h-screen flex items-center justify-center bg-gradient-to-br from-slate-950 via-slate-900 to-slate-800 text-white p-4">
      <div className="max-w-md w-full bg-slate-900/70 backdrop-blur-xl border border-slate-700 rounded-3xl shadow-2xl p-10 text-center">
        <div className="flex justify-center mb-6">
          <div className="p-4 rounded-2xl bg-cyan-500/10 border border-cyan-500">
            <ShieldCheck size={48} className="text-cyan-400" />
          </div>
        </div>

        <h1 className="text-3xl font-bold text-cyan-400 mb-2">Email Fraud Detector</h1>
        <p className="text-slate-300 mb-8 tracking-wide">
          AI-powered Gmail security & fraud detection system
        </p>

        <button
          onClick={handleLogin}
          className="w-full py-3 bg-cyan-500 hover:bg-cyan-400 text-slate-950 font-semibold rounded-xl transition-transform transform hover:scale-[1.02] flex items-center justify-center gap-2 shadow-lg"
        >
          <svg
            xmlns="http://www.w3.org/2000/svg"
            viewBox="0 0 24 24"
            fill="none"
            stroke="currentColor"
            strokeWidth="2"
            strokeLinecap="round"
            strokeLinejoin="round"
            className="w-5 h-5"
          >
            <path d="M4 4h16v16H4z" />
            <path d="M22 12l-10 7L2 12" />
          </svg>
          Sign in with Google
        </button>

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

