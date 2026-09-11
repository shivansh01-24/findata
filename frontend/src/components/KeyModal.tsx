import React, { useState } from 'react'
import { Key, CheckCircle, X, Shield, Sparkles } from 'lucide-react'

interface KeyModalProps {
  isOpen: boolean
  onClose: () => void
  currentConfigured: boolean
  onKeySaved: (newKey: string) => void
}

export const KeyModal: React.FC<KeyModalProps> = ({
  isOpen,
  onClose,
  currentConfigured,
  onKeySaved
}) => {
  const [apiKey, setApiKey] = useState('')
  const [saving, setSaving] = useState(false)
  const [statusMsg, setStatusMsg] = useState('')

  if (!isOpen) return null

  const handleSave = async (e: React.FormEvent) => {
    e.preventDefault()
    if (!apiKey.trim()) return

    setSaving(true)
    setStatusMsg('')

    try {
      const res = await fetch('/api/settings/openrouter-key', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ api_key: apiKey.trim() })
      })
      const data = await res.json()
      if (res.ok) {
        setStatusMsg('Key successfully configured!')
        onKeySaved(apiKey.trim())
        setTimeout(() => {
          onClose()
          setStatusMsg('')
        }, 1200)
      } else {
        setStatusMsg(data.detail || 'Failed to save key')
      }
    } catch (err: any) {
      setStatusMsg('Network error saving key')
    } finally {
      setSaving(false)
    }
  }

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/70 backdrop-blur-sm p-4">
      <div className="relative w-full max-w-md rounded-2xl border border-[#222f4c] bg-[#111726] p-6 shadow-2xl">
        <button
          onClick={onClose}
          className="absolute right-4 top-4 text-slate-400 hover:text-white"
        >
          <X className="h-5 w-5" />
        </button>

        <div className="flex items-center gap-3 mb-4">
          <div className="flex h-10 w-10 items-center justify-center rounded-xl bg-blue-600/20 text-blue-400 border border-blue-500/30">
            <Key className="h-5 w-5" />
          </div>
          <div>
            <h3 className="text-base font-bold text-white">OpenRouter API Key</h3>
            <p className="text-xs text-slate-400">Enables multi-model AI synthesis with free LLM fallback</p>
          </div>
        </div>

        <div className="mb-4 rounded-xl border border-blue-500/20 bg-blue-500/5 p-3 text-xs text-slate-300">
          <div className="flex items-center gap-2 font-semibold text-blue-400 mb-1">
            <Shield className="h-4 w-4" />
            <span>Resilient Multi-Model Architecture</span>
          </div>
          <p className="text-slate-400">
            Even without an API key, the platform operates in <strong>100% Deterministic Analytical Mode</strong> with zero hallucinations. Adding an OpenRouter key enables executive narrative explanations using free models:
          </p>
          <ul className="mt-2 list-disc list-inside space-y-0.5 text-slate-400 font-mono text-[11px]">
            <li>meta-llama/llama-3.3-70b-instruct:free</li>
            <li>google/gemini-2.0-flash-exp:free</li>
            <li>qwen/qwen-2.5-72b-instruct:free</li>
            <li>mistralai/mistral-small-24b-instruct-2501:free</li>
          </ul>
        </div>

        <form onSubmit={handleSave} className="space-y-4">
          <div>
            <label className="block text-xs font-semibold text-slate-300 mb-1.5">
              OpenRouter Key (sk-or-v1-...)
            </label>
            <input
              type="password"
              value={apiKey}
              onChange={(e) => setApiKey(e.target.value)}
              placeholder="sk-or-v1-..."
              className="w-full rounded-xl border border-[#222f4c] bg-[#161f33] px-3.5 py-2.5 text-xs text-white placeholder-slate-500 focus:border-blue-500 focus:outline-none focus:ring-1 focus:ring-blue-500 font-mono"
            />
          </div>

          {statusMsg && (
            <p className={`text-xs ${statusMsg.includes('success') ? 'text-emerald-400' : 'text-amber-400'}`}>
              {statusMsg}
            </p>
          )}

          <div className="flex items-center justify-end gap-3 pt-2">
            <button
              type="button"
              onClick={onClose}
              className="rounded-xl px-4 py-2 text-xs font-medium text-slate-400 hover:bg-[#161f33] hover:text-white transition-colors"
            >
              Cancel
            </button>
            <button
              type="submit"
              disabled={saving || !apiKey.trim()}
              className="flex items-center gap-2 rounded-xl bg-blue-600 px-4 py-2 text-xs font-semibold text-white hover:bg-blue-500 disabled:opacity-50 transition-all shadow-lg shadow-blue-600/30"
            >
              <Sparkles className="h-3.5 w-3.5" />
              <span>{saving ? 'Saving...' : 'Save & Activate'}</span>
            </button>
          </div>
        </form>
      </div>
    </div>
  )
}
