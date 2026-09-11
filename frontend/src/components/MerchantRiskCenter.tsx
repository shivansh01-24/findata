import React, { useEffect, useState } from 'react'
import { 
  Store, 
  Search, 
  Filter, 
  AlertTriangle, 
  CheckCircle2, 
  XCircle, 
  ExternalLink, 
  DollarSign, 
  FileText, 
  Clock, 
  X 
} from 'lucide-react'
import { STRReportModal } from './STRReportModal'

export const MerchantRiskCenter: React.FC = () => {
  const [merchants, setMerchants] = useState<any[]>([])
  const [selectedMerchant, setSelectedMerchant] = useState<any | null>(null)
  const [categoryFilter, setCategoryFilter] = useState('ALL')
  const [riskFilter, setRiskFilter] = useState('ALL')
  const [statusFilter, setStatusFilter] = useState('ALL')
  const [search, setSearch] = useState('')
  const [loading, setLoading] = useState(true)

  // STR Report Modal State
  const [isStrModalOpen, setIsStrModalOpen] = useState(false)
  const [strReportData, setStrReportData] = useState<any>(null)
  const [isStrLoading, setIsStrLoading] = useState(false)

  const handleExportMerchantSTR = (merchantId: string) => {
    setIsStrModalOpen(true)
    setIsStrLoading(true)
    fetch(`/api/reports/str/merchant/${merchantId}`)
      .then(res => res.json())
      .then(data => {
        setStrReportData(data)
        setIsStrLoading(false)
      })
      .catch(err => {
        console.error('Error fetching merchant STR:', err)
        setIsStrLoading(false)
      })
  }

  useEffect(() => {
    fetch('/api/analytics/merchants?limit=150')
      .then(res => res.json())
      .then(d => {
        setMerchants(d)
        setLoading(false)
      })
      .catch(err => {
        console.error('Error fetching merchants:', err)
        setLoading(false)
      })
  }, [])

  const handleInspect = async (mid: string) => {
    try {
      const res = await fetch(`/api/analytics/merchants/${mid}`)
      const data = await res.json()
      setSelectedMerchant(data)
    } catch (e) {
      console.error('Error loading merchant dossier:', e)
    }
  }

  const filtered = merchants.filter(m => {
    const matchesCat = categoryFilter === 'ALL' || m.merchant_category === categoryFilter
    const matchesRisk = riskFilter === 'ALL' || m.risk_level === riskFilter
    const matchesStatus = statusFilter === 'ALL' || m.merchant_status === statusFilter
    const matchesSearch = !search || 
      m.merchant_name.toLowerCase().includes(search.toLowerCase()) ||
      m.merchant_id.toLowerCase().includes(search.toLowerCase()) ||
      m.city.toLowerCase().includes(search.toLowerCase())
    return matchesCat && matchesRisk && matchesStatus && matchesSearch
  })

  return (
    <div className="space-y-6">
      {/* Top Header */}
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4">
        <div>
          <h2 className="text-xl font-extrabold text-white flex items-center gap-2">
            <Store className="h-6 w-6 text-purple-400" />
            <span>Merchant Risk Intelligence Center</span>
          </h2>
          <p className="text-xs text-slate-400 mt-0.5">
            Multivariate risk ranking, ticket size anomalies, and dispute concentration across 4,343 merchants.
          </p>
        </div>

        {/* Search */}
        <div className="relative w-full md:w-80">
          <Search className="absolute left-3 top-2.5 h-4 w-4 text-slate-500" />
          <input
            type="text"
            value={search}
            onChange={(e) => setSearch(e.target.value)}
            placeholder="Search merchant name, ID, or city..."
            className="w-full rounded-xl border border-[#222f4c] bg-[#111726] pl-9 pr-4 py-2 text-xs text-white placeholder-slate-500 focus:border-purple-500 focus:outline-none"
          />
        </div>
      </div>

      {/* Filter Bar */}
      <div className="flex flex-wrap items-center gap-3 rounded-2xl border border-[#222f4c] bg-[#111726] p-4 text-xs">
        <span className="font-semibold text-slate-400 flex items-center gap-1">
          <Filter className="h-3.5 w-3.5" /> Filters:
        </span>

        {/* Category */}
        <select
          value={categoryFilter}
          onChange={(e) => setCategoryFilter(e.target.value)}
          className="rounded-lg border border-[#222f4c] bg-[#161f33] px-3 py-1.5 text-slate-200 focus:border-purple-500 focus:outline-none"
        >
          <option value="ALL">All Categories</option>
          <option value="Grocery">Grocery</option>
          <option value="Pharmacy">Pharmacy</option>
          <option value="Restaurant">Restaurant</option>
          <option value="Transportation">Transportation</option>
          <option value="Hotel & Lodging">Hotel &amp; Lodging</option>
          <option value="Department Store">Department Store</option>
          <option value="Apparel">Apparel</option>
          <option value="Books & Stationery">Books &amp; Stationery</option>
          <option value="Miscellaneous Retail">Miscellaneous Retail</option>
          <option value="Telecom">Telecom</option>
        </select>

        {/* Risk Level */}
        <select
          value={riskFilter}
          onChange={(e) => setRiskFilter(e.target.value)}
          className="rounded-lg border border-[#222f4c] bg-[#161f33] px-3 py-1.5 text-slate-200 focus:border-purple-500 focus:outline-none"
        >
          <option value="ALL">All Risk Levels</option>
          <option value="CRITICAL">Critical (Score 80+)</option>
          <option value="HIGH">High (Score 60-79)</option>
          <option value="MEDIUM">Medium (Score 40-59)</option>
          <option value="LOW">Low (Score &lt;40)</option>
        </select>

        {/* Status */}
        <select
          value={statusFilter}
          onChange={(e) => setStatusFilter(e.target.value)}
          className="rounded-lg border border-[#222f4c] bg-[#161f33] px-3 py-1.5 text-slate-200 focus:border-purple-500 focus:outline-none"
        >
          <option value="ALL">All Operational Statuses</option>
          <option value="ACTIVE">Active</option>
          <option value="SUSPENDED">Suspended / Hold</option>
          <option value="INACTIVE">Inactive</option>
        </select>

        <span className="ml-auto text-slate-400 font-mono text-[11px]">
          Showing {filtered.length} merchants
        </span>
      </div>

      {/* Table */}
      <div className="overflow-x-auto rounded-2xl border border-[#222f4c] bg-[#111726] shadow-xl">
        <table className="w-full text-left text-xs">
          <thead className="border-b border-[#222f4c] bg-[#161f33]/60 text-slate-400 uppercase tracking-wider font-semibold">
            <tr>
              <th className="px-4 py-3.5">Merchant</th>
              <th className="px-4 py-3.5">Category &amp; City</th>
              <th className="px-4 py-3.5">Status</th>
              <th className="px-4 py-3.5">Ticket Size (Act vs Decl)</th>
              <th className="px-4 py-3.5">Disputes &amp; Volume</th>
              <th className="px-4 py-3.5">Dispute Rate</th>
              <th className="px-4 py-3.5">Risk Score</th>
              <th className="px-4 py-3.5 text-right">Action</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-[#222f4c]/60">
            {filtered.slice(0, 100).map(m => {
              const isCrit = m.risk_level === 'CRITICAL'
              const isHigh = m.risk_level === 'HIGH'
              return (
                <tr key={m.merchant_id} className="hover:bg-[#161f33]/40 transition-colors">
                  <td className="px-4 py-3">
                    <div className="font-bold text-white">{m.merchant_name}</div>
                    <div className="font-mono text-[11px] text-slate-400 flex items-center gap-1.5 mt-0.5">
                      <span>{m.merchant_id}</span>
                      {m.shared_settlement_account && (
                        <span className="rounded bg-red-500/20 px-1.5 py-0.2 text-[9px] font-bold text-red-400 border border-red-500/30">
                          SHARED ACC
                        </span>
                      )}
                    </div>
                  </td>
                  <td className="px-4 py-3">
                    <div className="text-slate-200">{m.merchant_category}</div>
                    <div className="text-slate-400 text-[11px]">{m.city}, {m.state}</div>
                  </td>
                  <td className="px-4 py-3">
                    <span className={`px-2 py-0.5 rounded text-[10px] font-bold border ${
                      m.merchant_status === 'ACTIVE' ? 'border-emerald-500/30 bg-emerald-500/10 text-emerald-400' :
                      m.merchant_status === 'SUSPENDED' ? 'border-red-500/30 bg-red-500/10 text-red-400' :
                      'border-slate-500/30 bg-slate-500/10 text-slate-400'
                    }`}>
                      {m.merchant_status}
                    </span>
                  </td>
                  <td className="px-4 py-3">
                    <div className="font-mono text-slate-200">₹{m.avg_ticket.toLocaleString()}</div>
                    <div className="text-[11px] text-slate-400">
                      Decl: ₹{m.declared_avg_ticket_size ? Number(m.declared_avg_ticket_size).toLocaleString() : 'N/A'}
                    </div>
                  </td>
                  <td className="px-4 py-3">
                    <div className="font-bold text-amber-400 mono">{m.cb_count} disputes</div>
                    <div className="text-[11px] text-slate-400 mono">₹{m.cb_volume.toLocaleString()}</div>
                  </td>
                  <td className="px-4 py-3">
                    <span className="font-extrabold text-white mono">{m.cb_rate_pct}%</span>
                  </td>
                  <td className="px-4 py-3">
                    <div className="flex items-center gap-2">
                      <span className={`px-2 py-0.5 rounded text-[11px] font-black border mono ${
                        isCrit ? 'border-red-500/40 bg-red-500/10 text-red-400' :
                        isHigh ? 'border-amber-500/40 bg-amber-500/10 text-amber-400' :
                        'border-blue-500/40 bg-blue-500/10 text-blue-400'
                      }`}>
                        {m.risk_score}
                      </span>
                    </div>
                  </td>
                  <td className="px-4 py-3 text-right">
                    <button
                      onClick={() => handleInspect(m.merchant_id)}
                      className="rounded-lg bg-purple-600/20 px-3 py-1.5 text-[11px] font-semibold text-purple-300 hover:bg-purple-600/30 border border-purple-500/30 transition-colors"
                    >
                      Dossier
                    </button>
                  </td>
                </tr>
              )
            })}
          </tbody>
        </table>
      </div>

      {/* Merchant Dossier Modal */}
      {selectedMerchant && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/80 backdrop-blur-sm p-4 overflow-y-auto">
          <div className="relative w-full max-w-3xl max-h-[90vh] overflow-y-auto rounded-2xl border border-[#222f4c] bg-[#111726] p-6 shadow-2xl space-y-5">
            <button
              onClick={() => setSelectedMerchant(null)}
              className="absolute right-4 top-4 text-slate-400 hover:text-white"
            >
              <X className="h-5 w-5" />
            </button>

            <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3 pr-8">
              <div className="flex items-center gap-3">
                <div className="flex h-12 w-12 items-center justify-center rounded-2xl bg-purple-600/20 text-purple-400 border border-purple-500/30">
                  <Store className="h-6 w-6" />
                </div>
                <div>
                  <h3 className="text-lg font-bold text-white flex items-center gap-2">
                    <span>{selectedMerchant.merchant_name}</span>
                    <span className="text-xs font-mono text-purple-400">({selectedMerchant.merchant_id})</span>
                  </h3>
                  <p className="text-xs text-slate-400">
                    {selectedMerchant.merchant_category} • {selectedMerchant.business_type} • {selectedMerchant.city}, {selectedMerchant.state}
                  </p>
                </div>
              </div>
              <button
                onClick={() => handleExportMerchantSTR(selectedMerchant.merchant_id)}
                className="flex items-center gap-1.5 rounded-xl bg-red-600/20 border border-red-500/30 px-3 py-1.5 text-xs font-bold text-red-400 hover:bg-red-600/30 transition-all shadow-md self-start sm:self-center"
              >
                <FileText className="h-3.5 w-3.5" />
                <span>Export FIU-IND STR</span>
              </button>
            </div>

            {/* Investigation Rationale Box */}
            <div className="rounded-xl border border-amber-500/30 bg-amber-500/10 p-4 text-xs text-amber-200">
              <span className="font-bold block mb-1 uppercase tracking-wider text-amber-400">
                Forensic Investigation Rationale:
              </span>
              <p className="leading-relaxed">{selectedMerchant.investigation_rationale}</p>
            </div>

            {/* Operational Details Grid */}
            <div className="grid grid-cols-2 sm:grid-cols-4 gap-3 text-xs">
              <div className="rounded-xl border border-[#222f4c] bg-[#161f33] p-3">
                <span className="block text-[11px] text-slate-400">Settlement Account</span>
                <span className="font-mono text-white font-bold">{selectedMerchant.settlement_account || 'Missing'}</span>
              </div>
              <div className="rounded-xl border border-[#222f4c] bg-[#161f33] p-3">
                <span className="block text-[11px] text-slate-400">Declared Ticket</span>
                <span className="font-mono text-white font-bold">₹{Number(selectedMerchant.declared_avg_ticket_size || 0).toLocaleString()}</span>
              </div>
              <div className="rounded-xl border border-[#222f4c] bg-[#161f33] p-3">
                <span className="block text-[11px] text-slate-400">Actual Avg Ticket</span>
                <span className="font-mono text-amber-400 font-bold">₹{selectedMerchant.avg_ticket.toLocaleString()}</span>
              </div>
              <div className="rounded-xl border border-[#222f4c] bg-[#161f33] p-3">
                <span className="block text-[11px] text-slate-400">Risk Score</span>
                <span className="font-mono text-red-400 font-extrabold">{selectedMerchant.risk_score} ({selectedMerchant.risk_level})</span>
              </div>
            </div>

            {/* Recent Disputes */}
            <div>
              <h4 className="text-xs font-bold text-white uppercase tracking-wider mb-2">
                Recent Customer Disputes ({selectedMerchant.recent_chargebacks?.length || 0})
              </h4>
              <div className="overflow-x-auto rounded-xl border border-[#222f4c] bg-[#161f33] text-xs">
                <table className="w-full text-left">
                  <thead className="border-b border-[#222f4c] bg-[#0a0d14]/50 text-slate-400 text-[11px]">
                    <tr>
                      <th className="p-2.5">Complaint ID</th>
                      <th className="p-2.5">User</th>
                      <th className="p-2.5">Disputed Amount</th>
                      <th className="p-2.5">Reason</th>
                      <th className="p-2.5">Severity</th>
                      <th className="p-2.5">Status</th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-[#222f4c]/50 text-[11px]">
                    {selectedMerchant.recent_chargebacks?.map((cb: any) => (
                      <tr key={cb.complaint_id}>
                        <td className="p-2.5 font-mono text-slate-300">{cb.complaint_id}</td>
                        <td className="p-2.5 font-mono text-slate-400">{cb.user_id}</td>
                        <td className="p-2.5 font-mono text-amber-400">₹{Number(cb.disputed_amount).toLocaleString()}</td>
                        <td className="p-2.5 text-slate-300">{cb.reason_category}</td>
                        <td className="p-2.5 font-semibold text-slate-200">{cb.severity}</td>
                        <td className="p-2.5 text-slate-400">{cb.resolution_status}</td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </div>
          </div>
        </div>
      )}

      {/* FIU-IND STR Report Modal */}
      <STRReportModal
        isOpen={isStrModalOpen}
        onClose={() => setIsStrModalOpen(false)}
        reportData={strReportData}
        isLoading={isStrLoading}
      />
    </div>
  )
}
