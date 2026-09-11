import React, { useEffect, useState } from 'react'
import { 
  Users, 
  Search, 
  Filter, 
  ShieldAlert, 
  AlertTriangle, 
  CheckCircle2, 
  XCircle, 
  CreditCard, 
  X 
} from 'lucide-react'

export const CustomerRiskCenter: React.FC = () => {
  const [customers, setCustomers] = useState<any[]>([])
  const [selectedCustomer, setSelectedCustomer] = useState<any | null>(null)
  const [kycFilter, setKycFilter] = useState('ALL')
  const [riskFilter, setRiskFilter] = useState('ALL')
  const [search, setSearch] = useState('')
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    fetch('/api/analytics/customers?limit=150')
      .then(res => res.json())
      .then(d => {
        setCustomers(d)
        setLoading(false)
      })
      .catch(err => {
        console.error('Error fetching customers:', err)
        setLoading(false)
      })
  }, [])

  const handleInspect = async (uid: string) => {
    try {
      const res = await fetch(`/api/analytics/customers/${uid}`)
      const data = await res.json()
      setSelectedCustomer(data)
    } catch (e) {
      console.error('Error loading customer dossier:', e)
    }
  }

  const filtered = customers.filter(c => {
    const matchesKyc = kycFilter === 'ALL' || c.kyc_status === kycFilter
    const matchesRisk = riskFilter === 'ALL' || c.risk_level === riskFilter
    const matchesSearch = !search || 
      c.full_name.toLowerCase().includes(search.toLowerCase()) ||
      c.user_id.toLowerCase().includes(search.toLowerCase()) ||
      c.city.toLowerCase().includes(search.toLowerCase())
    return matchesKyc && matchesRisk && matchesSearch
  })

  return (
    <div className="space-y-6">
      {/* Top Header */}
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4">
        <div>
          <h2 className="text-xl font-extrabold text-white flex items-center gap-2">
            <Users className="h-6 w-6 text-blue-400" />
            <span>Customer &amp; Synthetic Identity Risk Center</span>
          </h2>
          <p className="text-xs text-slate-400 mt-0.5">
            Surveillance of conflicting KYC records, shared Aadhaar credentials, and repeat dispute abusers across 28,920 customers.
          </p>
        </div>

        {/* Search */}
        <div className="relative w-full md:w-80">
          <Search className="absolute left-3 top-2.5 h-4 w-4 text-slate-500" />
          <input
            type="text"
            value={search}
            onChange={(e) => setSearch(e.target.value)}
            placeholder="Search customer name, ID, or city..."
            className="w-full rounded-xl border border-[#222f4c] bg-[#111726] pl-9 pr-4 py-2 text-xs text-white placeholder-slate-500 focus:border-blue-500 focus:outline-none"
          />
        </div>
      </div>

      {/* Filter Bar */}
      <div className="flex flex-wrap items-center gap-3 rounded-2xl border border-[#222f4c] bg-[#111726] p-4 text-xs">
        <span className="font-semibold text-slate-400 flex items-center gap-1">
          <Filter className="h-3.5 w-3.5" /> Filters:
        </span>

        {/* KYC Status */}
        <select
          value={kycFilter}
          onChange={(e) => setKycFilter(e.target.value)}
          className="rounded-lg border border-[#222f4c] bg-[#161f33] px-3 py-1.5 text-slate-200 focus:border-blue-500 focus:outline-none"
        >
          <option value="ALL">All KYC Statuses</option>
          <option value="VERIFIED">Verified</option>
          <option value="PENDING">Pending</option>
          <option value="REJECTED">Rejected</option>
        </select>

        {/* Risk Level */}
        <select
          value={riskFilter}
          onChange={(e) => setRiskFilter(e.target.value)}
          className="rounded-lg border border-[#222f4c] bg-[#161f33] px-3 py-1.5 text-slate-200 focus:border-blue-500 focus:outline-none"
        >
          <option value="ALL">All Risk Levels</option>
          <option value="CRITICAL">Critical (Score 80+)</option>
          <option value="HIGH">High (Score 60-79)</option>
          <option value="MEDIUM">Medium (Score 40-59)</option>
          <option value="LOW">Low (Score &lt;40)</option>
        </select>

        <span className="ml-auto text-slate-400 font-mono text-[11px]">
          Showing {filtered.length} customers
        </span>
      </div>

      {/* Table */}
      <div className="overflow-x-auto rounded-2xl border border-[#222f4c] bg-[#111726] shadow-xl">
        <table className="w-full text-left text-xs">
          <thead className="border-b border-[#222f4c] bg-[#161f33]/60 text-slate-400 uppercase tracking-wider font-semibold">
            <tr>
              <th className="px-4 py-3.5">Customer</th>
              <th className="px-4 py-3.5">PAN / Aadhaar</th>
              <th className="px-4 py-3.5">KYC Status</th>
              <th className="px-4 py-3.5">Entity Resolution</th>
              <th className="px-4 py-3.5">Disputes Filed</th>
              <th className="px-4 py-3.5">Disputed Amount</th>
              <th className="px-4 py-3.5">Risk Score</th>
              <th className="px-4 py-3.5 text-right">Action</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-[#222f4c]/60">
            {filtered.slice(0, 100).map(c => {
              const isCrit = c.risk_level === 'CRITICAL'
              const isHigh = c.risk_level === 'HIGH'
              return (
                <tr key={c.user_id} className="hover:bg-[#161f33]/40 transition-colors">
                  <td className="px-4 py-3">
                    <div className="font-bold text-white">{c.full_name}</div>
                    <div className="font-mono text-[11px] text-slate-400 mt-0.5">{c.user_id} • {c.city}, {c.state}</div>
                  </td>
                  <td className="px-4 py-3">
                    <div className="font-mono text-slate-200">{c.pan || 'Missing'}</div>
                    <div className="font-mono text-[11px] text-slate-400 flex items-center gap-1.5 mt-0.5">
                      <span>{c.aadhaar || 'Missing'}</span>
                      {c.shared_aadhaar_cluster && (
                        <span className="rounded bg-purple-500/20 px-1.5 py-0.2 text-[9px] font-bold text-purple-300 border border-purple-500/30">
                          SHARED AADHAAR
                        </span>
                      )}
                    </div>
                  </td>
                  <td className="px-4 py-3">
                    <span className={`px-2 py-0.5 rounded text-[10px] font-bold border ${
                      c.kyc_status === 'VERIFIED' ? 'border-emerald-500/30 bg-emerald-500/10 text-emerald-400' :
                      c.kyc_status === 'REJECTED' ? 'border-red-500/30 bg-red-500/10 text-red-400' :
                      'border-amber-500/30 bg-amber-500/10 text-amber-400'
                    }`}>
                      {c.kyc_status}
                    </span>
                  </td>
                  <td className="px-4 py-3">
                    <span className="text-slate-300 font-medium">{c.resolution_type}</span>
                    <div className="text-[10px] text-slate-500">{c.raw_record_count} raw rows merged</div>
                  </td>
                  <td className="px-4 py-3">
                    <span className="font-bold text-amber-400 mono">{c.cb_count} disputes</span>
                  </td>
                  <td className="px-4 py-3">
                    <span className="font-mono text-slate-200">₹{c.cb_volume.toLocaleString()}</span>
                  </td>
                  <td className="px-4 py-3">
                    <span className={`px-2 py-0.5 rounded text-[11px] font-black border mono ${
                      isCrit ? 'border-red-500/40 bg-red-500/10 text-red-400' :
                      isHigh ? 'border-amber-500/40 bg-amber-500/10 text-amber-400' :
                      'border-blue-500/40 bg-blue-500/10 text-blue-400'
                    }`}>
                      {c.risk_score}
                    </span>
                  </td>
                  <td className="px-4 py-3 text-right">
                    <button
                      onClick={() => handleInspect(c.user_id)}
                      className="rounded-lg bg-blue-600/20 px-3 py-1.5 text-[11px] font-semibold text-blue-300 hover:bg-blue-600/30 border border-blue-500/30 transition-colors"
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

      {/* Customer Dossier Modal */}
      {selectedCustomer && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/80 backdrop-blur-sm p-4 overflow-y-auto">
          <div className="relative w-full max-w-3xl max-h-[90vh] overflow-y-auto rounded-2xl border border-[#222f4c] bg-[#111726] p-6 shadow-2xl space-y-5">
            <button
              onClick={() => setSelectedCustomer(null)}
              className="absolute right-4 top-4 text-slate-400 hover:text-white"
            >
              <X className="h-5 w-5" />
            </button>

            <div className="flex items-center gap-3">
              <div className="flex h-12 w-12 items-center justify-center rounded-2xl bg-blue-600/20 text-blue-400 border border-blue-500/30">
                <Users className="h-6 w-6" />
              </div>
              <div>
                <h3 className="text-lg font-bold text-white flex items-center gap-2">
                  <span>{selectedCustomer.full_name}</span>
                  <span className="text-xs font-mono text-blue-400">({selectedCustomer.user_id})</span>
                </h3>
                <p className="text-xs text-slate-400">
                  Occupation: {selectedCustomer.occupation} • City: {selectedCustomer.city}, {selectedCustomer.state}
                </p>
              </div>
            </div>

            {/* Investigation Rationale Box */}
            <div className="rounded-xl border border-blue-500/30 bg-blue-500/10 p-4 text-xs text-blue-200">
              <span className="font-bold block mb-1 uppercase tracking-wider text-blue-400">
                Identity Risk Assessment &amp; Conflict Rationale:
              </span>
              <p className="leading-relaxed">{selectedCustomer.investigation_rationale}</p>
            </div>

            {/* Grid */}
            <div className="grid grid-cols-2 sm:grid-cols-4 gap-3 text-xs">
              <div className="rounded-xl border border-[#222f4c] bg-[#161f33] p-3">
                <span className="block text-[11px] text-slate-400">Monthly Income</span>
                <span className="font-mono text-white font-bold">₹{Number(selectedCustomer.monthly_income || 0).toLocaleString()}</span>
              </div>
              <div className="rounded-xl border border-[#222f4c] bg-[#161f33] p-3">
                <span className="block text-[11px] text-slate-400">Aadhaar Status</span>
                <span className="font-mono text-purple-400 font-bold">{selectedCustomer.aadhaar_flag}</span>
              </div>
              <div className="rounded-xl border border-[#222f4c] bg-[#161f33] p-3">
                <span className="block text-[11px] text-slate-400">PAN Status</span>
                <span className="font-mono text-white font-bold">{selectedCustomer.pan_flag}</span>
              </div>
              <div className="rounded-xl border border-[#222f4c] bg-[#161f33] p-3">
                <span className="block text-[11px] text-slate-400">Risk Score</span>
                <span className="font-mono text-red-400 font-extrabold">{selectedCustomer.risk_score} ({selectedCustomer.risk_level})</span>
              </div>
            </div>

            {/* Recent Disputes */}
            <div>
              <h4 className="text-xs font-bold text-white uppercase tracking-wider mb-2">
                Disputes Raised by User ({selectedCustomer.recent_chargebacks?.length || 0})
              </h4>
              <div className="overflow-x-auto rounded-xl border border-[#222f4c] bg-[#161f33] text-xs">
                <table className="w-full text-left">
                  <thead className="border-b border-[#222f4c] bg-[#0a0d14]/50 text-slate-400 text-[11px]">
                    <tr>
                      <th className="p-2.5">Complaint ID</th>
                      <th className="p-2.5">Merchant</th>
                      <th className="p-2.5">Disputed Amount</th>
                      <th className="p-2.5">Reason</th>
                      <th className="p-2.5">Severity</th>
                      <th className="p-2.5">Status</th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-[#222f4c]/50 text-[11px]">
                    {selectedCustomer.recent_chargebacks?.map((cb: any) => (
                      <tr key={cb.complaint_id}>
                        <td className="p-2.5 font-mono text-slate-300">{cb.complaint_id}</td>
                        <td className="p-2.5 font-mono text-slate-400">{cb.merchant_id}</td>
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
    </div>
  )
}
