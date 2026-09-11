import React, { useState } from 'react'
import { 
  X, 
  Download, 
  Copy, 
  Check, 
  ShieldAlert, 
  FileText, 
  Code, 
  ExternalLink,
  Printer
} from 'lucide-react'

interface STRReportModalProps {
  isOpen: boolean
  onClose: () => void
  reportData: any
  isLoading?: boolean
}

export const STRReportModal: React.FC<STRReportModalProps> = ({
  isOpen,
  onClose,
  reportData,
  isLoading = false
}) => {
  const [activeView, setActiveView] = useState<'markdown' | 'json'>('markdown')
  const [copied, setCopied] = useState(false)

  if (!isOpen) return null

  const handleCopy = () => {
    const textToCopy = activeView === 'markdown' 
      ? (reportData?.markdown_dossier || '') 
      : JSON.stringify(reportData, null, 2)
    navigator.clipboard.writeText(textToCopy)
    setCopied(true)
    setTimeout(() => setCopied(false), 2000)
  }

  const handleDownload = (format: 'md' | 'json') => {
    if (!reportData) return
    const filename = `${reportData?.report_metadata?.report_reference?.replace(/\//g, '_') || 'FIU_STR_DOSSIER'}.${format}`
    const content = format === 'md' ? reportData.markdown_dossier : JSON.stringify(reportData, null, 2)
    const blob = new Blob([content], { type: format === 'md' ? 'text/markdown' : 'application/json' })
    const url = URL.createObjectURL(blob)
    const a = document.createElement('a')
    a.href = url
    a.download = filename
    document.body.appendChild(a)
    a.click()
    document.body.removeChild(a)
    URL.revokeObjectURL(url)
  }

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/80 backdrop-blur-sm p-4">
      <div className="relative w-full max-w-4xl max-h-[90vh] flex flex-col rounded-2xl bg-[#0e1320] border border-blue-500/30 shadow-2xl shadow-blue-500/10">
        
        {/* Header */}
        <div className="flex items-center justify-between border-b border-[#222f4c] px-6 py-4 bg-[#121829]">
          <div className="flex items-center gap-3">
            <div className="flex h-10 w-10 items-center justify-center rounded-xl bg-red-500/10 border border-red-500/30 text-red-400">
              <ShieldAlert className="h-5 w-5" />
            </div>
            <div>
              <div className="flex items-center gap-2">
                <h3 className="text-base font-bold text-white">FIU-IND Suspicious Transaction Report (STR)</h3>
                <span className="rounded bg-red-500/20 px-2 py-0.5 text-[10px] font-bold text-red-400 border border-red-500/30">
                  CONFIDENTIAL // PMLA SEC 12
                </span>
              </div>
              <p className="text-xs text-slate-400 font-mono">
                {reportData?.report_metadata?.report_reference || 'Generating Case Reference...'}
              </p>
            </div>
          </div>

          <div className="flex items-center gap-2">
            {/* View Switcher */}
            <div className="flex items-center rounded-lg bg-[#182137] p-1 border border-[#2a3a5e] text-xs">
              <button
                onClick={() => setActiveView('markdown')}
                className={`flex items-center gap-1.5 rounded px-2.5 py-1 transition-all ${
                  activeView === 'markdown' ? 'bg-blue-600 text-white font-semibold' : 'text-slate-400 hover:text-slate-200'
                }`}
              >
                <FileText className="h-3.5 w-3.5" />
                <span>Legal Brief</span>
              </button>
              <button
                onClick={() => setActiveView('json')}
                className={`flex items-center gap-1.5 rounded px-2.5 py-1 transition-all ${
                  activeView === 'json' ? 'bg-blue-600 text-white font-semibold' : 'text-slate-400 hover:text-slate-200'
                }`}
              >
                <Code className="h-3.5 w-3.5" />
                <span>JSON</span>
              </button>
            </div>

            {/* Actions */}
            <button
              onClick={handleCopy}
              className="flex items-center gap-1.5 rounded-lg border border-[#2a3a5e] bg-[#182137] px-3 py-1.5 text-xs text-slate-200 hover:bg-[#202b48] transition-colors"
              title="Copy to Clipboard"
            >
              {copied ? <Check className="h-3.5 w-3.5 text-emerald-400" /> : <Copy className="h-3.5 w-3.5" />}
              <span>{copied ? 'Copied' : 'Copy'}</span>
            </button>

            <button
              onClick={() => handleDownload('md')}
              className="flex items-center gap-1.5 rounded-lg bg-blue-600 px-3 py-1.5 text-xs font-semibold text-white hover:bg-blue-500 shadow-md shadow-blue-600/30 transition-colors"
            >
              <Download className="h-3.5 w-3.5" />
              <span>Download (.md)</span>
            </button>

            <button
              onClick={onClose}
              className="rounded-lg p-1.5 text-slate-400 hover:bg-[#1f2a44] hover:text-white transition-colors"
            >
              <X className="h-5 w-5" />
            </button>
          </div>
        </div>

        {/* Content Body */}
        <div className="flex-1 overflow-y-auto p-6 font-mono text-xs">
          {isLoading ? (
            <div className="flex h-64 flex-col items-center justify-center gap-3">
              <div className="h-8 w-8 animate-spin rounded-full border-2 border-blue-500 border-t-transparent" />
              <p className="text-slate-400">Compiling statutory FIU-IND regulatory dossier...</p>
            </div>
          ) : activeView === 'markdown' ? (
            <div className="prose prose-invert max-w-none space-y-4 font-sans text-slate-300">
              <div className="rounded-xl border border-blue-500/20 bg-blue-500/5 p-4 text-xs">
                <div className="grid grid-cols-2 md:grid-cols-4 gap-3 text-slate-300">
                  <div>
                    <span className="text-slate-500 block">Reporting Entity</span>
                    <span className="font-semibold text-white">TransOrg UPI Switch</span>
                  </div>
                  <div>
                    <span className="text-slate-500 block">Registration No</span>
                    <span className="font-mono text-blue-400">FIU-IND-PSO-2026-UPI</span>
                  </div>
                  <div>
                    <span className="text-slate-500 block">Filing Date</span>
                    <span className="text-white">{reportData?.report_metadata?.filing_date || 'Current'}</span>
                  </div>
                  <div>
                    <span className="text-slate-500 block">Statutory Mandate</span>
                    <span className="text-emerald-400 font-semibold">PMLA 2002 Sec 12</span>
                  </div>
                </div>
              </div>

              <div className="whitespace-pre-wrap font-mono text-xs leading-relaxed bg-[#090d16] p-5 rounded-xl border border-[#1e293b] text-slate-200">
                {reportData?.markdown_dossier || 'No report dossier available.'}
              </div>
            </div>
          ) : (
            <pre className="p-4 rounded-xl bg-[#090d16] border border-[#1e293b] text-emerald-400 overflow-x-auto text-[11px] leading-relaxed">
              {JSON.stringify(reportData, null, 2)}
            </pre>
          )}
        </div>

        {/* Footer Note */}
        <div className="flex items-center justify-between border-t border-[#222f4c] px-6 py-3 bg-[#0c101a] text-[11px] text-slate-400">
          <span>Official filing format compliant with FIU-IND FINnet 2.0 XML schema and RBI digital payment guidelines.</span>
          <button 
            onClick={() => handleDownload('json')}
            className="text-blue-400 hover:text-blue-300 font-semibold flex items-center gap-1"
          >
            <span>Export Machine JSON</span>
            <ExternalLink className="h-3 w-3" />
          </button>
        </div>

      </div>
    </div>
  )
}
