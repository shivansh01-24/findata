import React, { useState, useEffect } from 'react'
import { Navbar } from './components/Navbar'
import { ExecutiveOverview } from './components/ExecutiveOverview'
import { FraudRingExplorer } from './components/FraudRingExplorer'
import { MerchantRiskCenter } from './components/MerchantRiskCenter'
import { CustomerRiskCenter } from './components/CustomerRiskCenter'
import { RiskSimulator } from './components/RiskSimulator'
import { DataRescueAudit } from './components/DataRescueAudit'
import { AgentDrawer } from './components/AgentDrawer'
import { KeyModal } from './components/KeyModal'
import { ShieldCheck, GitBranch, ExternalLink } from 'lucide-react'

export function App() {
  const [activeTab, setActiveTab] = useState<string>('overview')
  const [isAgentOpen, setIsAgentOpen] = useState<boolean>(false)
  const [isKeyModalOpen, setIsKeyModalOpen] = useState<boolean>(false)
  const [openrouterConfigured, setOpenrouterConfigured] = useState<boolean>(false)

  // Fetch health and key status on mount
  useEffect(() => {
    fetch('/api/health')
      .then(res => res.json())
      .then(data => {
        setOpenrouterConfigured(data.openrouter_key_configured)
      })
      .catch(err => console.error('Error checking health:', err))
  }, [])

  return (
    <div className="min-h-screen bg-[#0a0d14] text-slate-100 flex flex-col font-['Plus_Jakarta_Sans',sans-serif]">
      {/* Navbar */}
      <Navbar
        activeTab={activeTab}
        setActiveTab={setActiveTab}
        isAgentOpen={isAgentOpen}
        setIsAgentOpen={setIsAgentOpen}
        onOpenKeyModal={() => setIsKeyModalOpen(true)}
        openrouterConfigured={openrouterConfigured}
      />

      {/* Main Content Area */}
      <main className="flex-1 max-w-7xl w-full mx-auto p-6">
        {activeTab === 'overview' && <ExecutiveOverview />}
        {activeTab === 'rings' && <FraudRingExplorer />}
        {activeTab === 'merchants' && <MerchantRiskCenter />}
        {activeTab === 'customers' && <CustomerRiskCenter />}
        {activeTab === 'simulator' && <RiskSimulator />}
        {activeTab === 'data_rescue' && <DataRescueAudit />}
      </main>

      {/* Footer with Rubric & Audit Assurance */}
      <footer className="w-full border-t border-[#222f4c] bg-[#0c101a] py-6 px-6 text-xs text-slate-400">
        <div className="max-w-7xl mx-auto flex flex-col md:flex-row items-center justify-between gap-4">
          <div className="flex items-center gap-2">
            <ShieldCheck className="h-4 w-4 text-emerald-400" />
            <span>TransOrg AgentIQ Datathon Track 1 • FinTech &amp; BFSI UPI Fraud Intelligence Platform</span>
          </div>
          <div className="flex items-center gap-4">
            <span className="text-slate-500">Grounded deterministic layer with multi-model fallback</span>
            <a
              href="https://github.com/shivansh01-24/findata"
              target="_blank"
              rel="noreferrer"
              className="flex items-center gap-1.5 text-blue-400 hover:text-blue-300 font-semibold"
            >
              <GitBranch className="h-4 w-4" />
              <span>GitHub Repository</span>
              <ExternalLink className="h-3 w-3" />
            </a>
          </div>
        </div>
      </footer>

      {/* Agent Drawer */}
      <AgentDrawer
        isOpen={isAgentOpen}
        onClose={() => setIsAgentOpen(false)}
        openrouterConfigured={openrouterConfigured}
      />

      {/* API Key Modal */}
      <KeyModal
        isOpen={isKeyModalOpen}
        onClose={() => setIsKeyModalOpen(false)}
        currentConfigured={openrouterConfigured}
        onKeySaved={() => setOpenrouterConfigured(true)}
      />
    </div>
  )
}

export default App
