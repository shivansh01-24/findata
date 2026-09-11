import React from 'react'
import { 
  ShieldAlert, 
  BarChart3, 
  Network, 
  Store, 
  Users, 
  Database, 
  Bot, 
  Key, 
  CheckCircle2, 
  AlertTriangle 
} from 'lucide-react'

interface NavbarProps {
  activeTab: string
  setActiveTab: (tab: string) => void
  isAgentOpen: boolean
  setIsAgentOpen: (open: boolean) => void
  onOpenKeyModal: () => void
  openrouterConfigured: boolean
}

export const Navbar: React.FC<NavbarProps> = ({
  activeTab,
  setActiveTab,
  isAgentOpen,
  setIsAgentOpen,
  onOpenKeyModal,
  openrouterConfigured
}) => {
  const tabs = [
    { id: 'overview', label: 'Executive Overview', icon: BarChart3 },
    { id: 'rings', label: 'Fraud Ring Explorer', icon: Network },
    { id: 'merchants', label: 'Merchant Risk Center', icon: Store },
    { id: 'customers', label: 'Customer / Identity Risk', icon: Users },
    { id: 'data_rescue', label: 'Data Rescue & Audit', icon: Database },
  ]

  return (
    <header className="sticky top-0 z-40 w-full border-b border-[#222f4c] bg-[#0a0d14]/90 backdrop-blur-md">
      <div className="flex h-16 items-center justify-between px-6">
        {/* Logo & Title */}
        <div className="flex items-center gap-3">
          <div className="flex h-10 w-10 items-center justify-center rounded-xl bg-gradient-to-tr from-blue-600 to-indigo-500 shadow-lg shadow-blue-500/20">
            <ShieldAlert className="h-6 w-6 text-white" />
          </div>
          <div>
            <div className="flex items-center gap-2">
              <span className="font-extrabold text-white tracking-tight text-lg">AGENTIQ</span>
              <span className="rounded bg-blue-500/10 px-2 py-0.5 text-xs font-semibold text-blue-400 border border-blue-500/20">TRACK 1</span>
            </div>
            <p className="text-xs text-slate-400">UPI Fraud & Merchant Risk Platform</p>
          </div>
        </div>

        {/* View Switcher Tabs */}
        <nav className="flex items-center gap-1 rounded-xl bg-[#111726] p-1 border border-[#222f4c]">
          {tabs.map((tab) => {
            const Icon = tab.icon
            const isActive = activeTab === tab.id
            return (
              <button
                key={tab.id}
                onClick={() => setActiveTab(tab.id)}
                className={`flex items-center gap-2 rounded-lg px-3.5 py-1.5 text-xs font-medium transition-all ${
                  isActive
                    ? 'bg-blue-600 text-white shadow-md shadow-blue-600/30'
                    : 'text-slate-400 hover:text-slate-200 hover:bg-[#161f33]'
                }`}
              >
                <Icon className="h-4 w-4" />
                <span>{tab.label}</span>
              </button>
            )
          })}
        </nav>

        {/* Actions & Status */}
        <div className="flex items-center gap-3">
          {/* AI Model Status Badge */}
          <button
            onClick={onOpenKeyModal}
            className={`flex items-center gap-1.5 rounded-lg px-2.5 py-1.5 text-xs font-medium border transition-colors ${
              openrouterConfigured
                ? 'border-emerald-500/30 bg-emerald-500/10 text-emerald-400 hover:bg-emerald-500/20'
                : 'border-amber-500/30 bg-amber-500/10 text-amber-400 hover:bg-amber-500/20'
            }`}
            title="Configure OpenRouter API Key"
          >
            {openrouterConfigured ? (
              <>
                <CheckCircle2 className="h-3.5 w-3.5 text-emerald-400" />
                <span>OpenRouter Live</span>
              </>
            ) : (
              <>
                <AlertTriangle className="h-3.5 w-3.5 text-amber-400" />
                <span>Deterministic Mode</span>
              </>
            )}
            <Key className="h-3 w-3 ml-1 opacity-70" />
          </button>

          {/* Ask Fraud Agent Button */}
          <button
            onClick={() => setIsAgentOpen(!isAgentOpen)}
            className={`flex items-center gap-2 rounded-xl px-4 py-2 text-xs font-semibold shadow-lg transition-all ${
              isAgentOpen
                ? 'bg-indigo-600 text-white shadow-indigo-500/30'
                : 'bg-gradient-to-r from-blue-600 to-indigo-600 text-white hover:opacity-95 shadow-blue-500/25 hover:shadow-blue-500/40'
            }`}
          >
            <Bot className="h-4 w-4 animate-pulse" />
            <span>Ask Fraud Agent</span>
          </button>
        </div>
      </div>
    </header>
  )
}
