import React, { useEffect, useState } from 'react'
import { 
  Network, 
  ShieldAlert, 
  Search, 
  AlertTriangle, 
  Building2, 
  Users, 
  ArrowRight, 
  DollarSign, 
  Layers, 
  ExternalLink, 
  CheckCircle2, 
  Info 
} from 'lucide-react'
import { NetworkGraph, GraphNode } from './NetworkGraph'

export const FraudRingExplorer: React.FC = () => {
  const [rings, setRings] = useState<any[]>([])
  const [selectedRingId, setSelectedRingId] = useState<string>('')
  const [graphData, setGraphData] = useState<any>(null)
  const [selectedNode, setSelectedNode] = useState<GraphNode | null>(null)
  const [filterType, setFilterType] = useState<string>('ALL')
  const [searchQuery, setSearchQuery] = useState<string>('')
  const [loading, setLoading] = useState(true)
  const [graphLoading, setGraphLoading] = useState(false)

  // 1. Fetch all rings
  useEffect(() => {
    fetch('/api/analytics/fraud-rings?limit=100')
      .then(res => res.json())
      .then(data => {
        setRings(data)
        if (data.length > 0) {
          setSelectedRingId(data[0].ring_id)
        }
        setLoading(false)
      })
      .catch(err => {
        console.error('Error fetching rings:', err)
        setLoading(false)
      })
  }, [])

  // 2. Fetch graph data for selected ring
  useEffect(() => {
    if (!selectedRingId) return
    setGraphLoading(true)
    setSelectedNode(null)
    fetch(`/api/analytics/fraud-rings/${selectedRingId}/graph`)
      .then(res => res.json())
      .then(data => {
        setGraphData(data)
        setGraphLoading(false)
      })
      .catch(err => {
        console.error('Error fetching ring graph:', err)
        setGraphLoading(false)
      })
  }, [selectedRingId])

  const filteredRings = rings.filter(r => {
    const matchesType = filterType === 'ALL' || r.ring_type.toLowerCase().includes(filterType.toLowerCase())
    const matchesSearch = !searchQuery || 
      r.ring_name.toLowerCase().includes(searchQuery.toLowerCase()) ||
      r.ring_id.toLowerCase().includes(searchQuery.toLowerCase()) ||
      r.anchor_attribute.toLowerCase().includes(searchQuery.toLowerCase())
    return matchesType && matchesSearch
  })

  const currentRing = rings.find(r => r.ring_id === selectedRingId)

  if (loading) {
    return (
      <div className="flex h-96 items-center justify-center">
        <div className="flex flex-col items-center gap-3">
          <div className="h-8 w-8 animate-spin rounded-full border-2 border-indigo-500 border-t-transparent"></div>
          <p className="text-xs text-slate-400">Synthesizing Network Graph Topology...</p>
        </div>
      </div>
    )
  }

  return (
    <div className="space-y-6">
      {/* Top Header & Typology Filters */}
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4">
        <div>
          <h2 className="text-xl font-extrabold text-white flex items-center gap-2">
            <Network className="h-6 w-6 text-indigo-400" />
            <span>Fraud Ring &amp; Network Intelligence</span>
          </h2>
          <p className="text-xs text-slate-400 mt-0.5">
            295 graph-derived syndicates identified across shared accounts, synthetic identities, and bust-out rings.
          </p>
        </div>

        {/* Filter Pills */}
        <div className="flex items-center gap-2 overflow-x-auto pb-1">
          {['ALL', 'Shared Settlement', 'Synthetic Identity', 'Bust-Out'].map(t => (
            <button
              key={t}
              onClick={() => setFilterType(t)}
              className={`rounded-xl px-3 py-1.5 text-xs font-semibold whitespace-nowrap transition-all border ${
                filterType === t
                  ? 'bg-indigo-600 text-white border-indigo-500 shadow-md shadow-indigo-600/30'
                  : 'border-[#222f4c] bg-[#111726] text-slate-400 hover:text-slate-200'
              }`}
            >
              {t === 'ALL' ? 'All Networks (295)' : t}
            </button>
          ))}
        </div>
      </div>

      {/* Main Investigation Split View */}
      <div className="grid grid-cols-1 lg:grid-cols-12 gap-6">
        {/* Left Column: Ring Selector List (4 cols) */}
        <div className="lg:col-span-4 rounded-2xl border border-[#222f4c] bg-[#111726] p-4 flex flex-col h-[750px]">
          {/* Search Bar */}
          <div className="relative mb-3">
            <Search className="absolute left-3 top-2.5 h-4 w-4 text-slate-500" />
            <input
              type="text"
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              placeholder="Search rings by ID, account, or merchant..."
              className="w-full rounded-xl border border-[#222f4c] bg-[#161f33] pl-9 pr-3.5 py-2 text-xs text-white placeholder-slate-500 focus:border-indigo-500 focus:outline-none"
            />
          </div>

          <div className="text-[11px] font-semibold text-slate-400 px-1 mb-2">
            Identified Syndicates ({filteredRings.length})
          </div>

          {/* List */}
          <div className="flex-1 overflow-y-auto space-y-2 pr-1">
            {filteredRings.map(r => {
              const isSelected = r.ring_id === selectedRingId
              return (
                <div
                  key={r.ring_id}
                  onClick={() => setSelectedRingId(r.ring_id)}
                  className={`p-3 rounded-xl border transition-all cursor-pointer ${
                    isSelected
                      ? 'border-indigo-500 bg-indigo-950/30 shadow-md shadow-indigo-950/40'
                      : 'border-[#222f4c] bg-[#161f33] hover:border-slate-600'
                  }`}
                >
                  <div className="flex items-center justify-between mb-1">
                    <span className="font-mono text-[11px] text-indigo-400 font-bold">{r.ring_id}</span>
                    <span className={`px-2 py-0.5 rounded text-[10px] font-extrabold border ${
                      r.risk_score >= 85 ? 'border-red-500/40 bg-red-500/10 text-red-400' :
                      r.risk_score >= 70 ? 'border-amber-500/40 bg-amber-500/10 text-amber-400' :
                      'border-blue-500/40 bg-blue-500/10 text-blue-400'
                    }`}>
                      Risk {r.risk_score}
                    </span>
                  </div>
                  <h4 className="text-xs font-bold text-white line-clamp-1">{r.ring_name}</h4>
                  <p className="text-[11px] text-slate-400 mt-0.5 line-clamp-1">{r.anchor_attribute}</p>
                  <div className="flex items-center justify-between text-[11px] text-slate-400 mt-2 pt-2 border-t border-[#222f4c]/60">
                    <span>{r.merchant_count} merchants</span>
                    <span>{r.customer_count} users</span>
                    <span className="text-amber-400 font-semibold">{r.chargeback_count} disputes</span>
                  </div>
                </div>
              )
            })}
          </div>
        </div>

        {/* Right Column: Interactive Graph & Dossier (8 cols) */}
        <div className="lg:col-span-8 space-y-6">
          {/* Interactive Graph Canvas */}
          <div className="rounded-2xl border border-[#222f4c] bg-[#111726] p-5 shadow-xl">
            <div className="flex items-center justify-between mb-3">
              <div>
                <h3 className="text-base font-bold text-white flex items-center gap-2">
                  <span>{currentRing?.ring_name}</span>
                  <span className="text-xs font-mono text-indigo-400">({currentRing?.ring_id})</span>
                </h3>
                <p className="text-xs text-slate-400">
                  Interactive topology map. Click any node to inspect entity dossier and transactions.
                </p>
              </div>
              <span className="text-xs text-slate-400">
                {graphData?.nodes?.length || 0} nodes | {graphData?.edges?.length || 0} edges
              </span>
            </div>

            {graphLoading ? (
              <div className="h-[520px] flex items-center justify-center bg-[#0c101a] rounded-2xl border border-[#222f4c]">
                <div className="h-8 w-8 animate-spin rounded-full border-2 border-indigo-500 border-t-transparent"></div>
              </div>
            ) : (
              <NetworkGraph
                nodes={graphData?.nodes || []}
                edges={graphData?.edges || []}
                onNodeClick={(node) => setSelectedNode(node)}
                selectedNodeId={selectedNode?.id}
              />
            )}
          </div>

          {/* Explainable Evidence & Action Dossier */}
          {currentRing && (
            <div className="rounded-2xl border border-[#222f4c] bg-[#111726] p-6 shadow-xl space-y-4">
              <div className="flex items-center justify-between border-b border-[#222f4c] pb-3">
                <div className="flex items-center gap-2.5">
                  <ShieldAlert className="h-5 w-5 text-amber-400" />
                  <h4 className="text-sm font-bold text-white">Forensic Evidence &amp; Recommended Action</h4>
                </div>
                <span className="rounded-lg bg-red-500/10 px-2.5 py-1 text-xs font-bold text-red-400 border border-red-500/20">
                  INVESTIGATION PRIORITY: {currentRing.severity}
                </span>
              </div>

              {/* Why Flagged */}
              <div>
                <span className="block text-xs font-bold uppercase tracking-wider text-slate-400 mb-1">
                  Why Flagged (Algorithm Justification)
                </span>
                <p className="text-xs text-slate-200 bg-[#161f33] p-3 rounded-xl border border-[#222f4c] leading-relaxed">
                  {currentRing.why_flagged}
                </p>
              </div>

              {/* Recommendation */}
              <div>
                <span className="block text-xs font-bold uppercase tracking-wider text-indigo-400 mb-1">
                  Actionable Operational Protocol
                </span>
                <p className="text-xs text-slate-200 bg-indigo-950/20 p-3 rounded-xl border border-indigo-500/30 leading-relaxed">
                  {currentRing.recommendation}
                </p>
              </div>

              {/* Entity Breakdown Stats */}
              <div className="grid grid-cols-2 sm:grid-cols-4 gap-3 pt-2">
                <div className="rounded-xl border border-[#222f4c] bg-[#161f33] p-3">
                  <span className="block text-[11px] text-slate-400">Total Volume</span>
                  <span className="text-sm font-extrabold text-white mono">₹{currentRing.transaction_volume.toLocaleString()}</span>
                </div>
                <div className="rounded-xl border border-[#222f4c] bg-[#161f33] p-3">
                  <span className="block text-[11px] text-slate-400">Transactions</span>
                  <span className="text-sm font-extrabold text-white mono">{currentRing.transaction_count}</span>
                </div>
                <div className="rounded-xl border border-[#222f4c] bg-[#161f33] p-3">
                  <span className="block text-[11px] text-slate-400">Chargebacks</span>
                  <span className="text-sm font-extrabold text-amber-400 mono">{currentRing.chargeback_count}</span>
                </div>
                <div className="rounded-xl border border-[#222f4c] bg-[#161f33] p-3">
                  <span className="block text-[11px] text-slate-400">Dispute Rate</span>
                  <span className="text-sm font-extrabold text-red-400 mono">{currentRing.chargeback_rate_pct}%</span>
                </div>
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  )
}
