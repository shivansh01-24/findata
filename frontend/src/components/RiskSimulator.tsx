import React, { useState, useEffect } from 'react'
import { 
  Sliders, 
  ShieldAlert, 
  TrendingUp, 
  AlertTriangle, 
  CheckCircle2, 
  ArrowRight, 
  FileText, 
  RefreshCw, 
  Zap,
  Info
} from 'lucide-react'
import { 
  BarChart, 
  Bar, 
  XAxis, 
  YAxis, 
  Tooltip, 
  ResponsiveContainer, 
  Legend, 
  CartesianGrid 
} from 'recharts'
import { STRReportModal } from './STRReportModal'

export const RiskSimulator: React.FC = () => {
  const [cbThreshold, setCbThreshold] = useState<number>(20)
  const [ticketMultiplier, setTicketMultiplier] = useState<number>(2.0)
  const [muleThreshold, setMuleThreshold] = useState<number>(2)
  const [minTxns, setMinTxns] = useState<number>(3)

  const [simData, setSimData] = useState<any>(null)
  const [isLoading, setIsLoading] = useState<boolean>(false)

  // STR Report Modal State
  const [selectedMchForStr, setSelectedMchForStr] = useState<string | null>(null)
  const [strReportData, setStrReportData] = useState<any>(null)
  const [isStrLoading, setIsStrLoading] = useState<boolean>(false)

  const runSimulation = () => {
    setIsLoading(true)
    fetch('/api/analytics/simulate-policy', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        chargeback_threshold_pct: cbThreshold,
        ticket_multiplier: ticketMultiplier,
        mule_sharing_threshold: muleThreshold,
        min_txns_evaluated: minTxns
      })
    })
      .then(res => res.json())
      .then(data => {
        setSimData(data)
        setIsLoading(false)
      })
      .catch(err => {
        console.error('Error simulating policy:', err)
        setIsLoading(false)
      })
  }

  useEffect(() => {
    runSimulation()
  }, [cbThreshold, ticketMultiplier, muleThreshold, minTxns])

  const handleOpenSTR = (merchantId: string) => {
    setSelectedMchForStr(merchantId)
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

  const chartData = simData ? [
    {
      metric: 'Merchants Flagged',
      Baseline: simData.baseline_metrics.flagged_merchants,
      Simulated: simData.simulated_metrics.flagged_merchants
    },
    {
      metric: 'Disputes Captured',
      Baseline: simData.baseline_metrics.chargebacks_captured,
      Simulated: simData.simulated_metrics.chargebacks_captured
    }
  ] : []

  return (
    <div className="space-y-6">
      {/* Header Banner */}
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 rounded-2xl bg-gradient-to-r from-[#10172a] via-[#131d36] to-[#0f172a] p-6 border border-blue-500/20 shadow-xl shadow-blue-500/5">
        <div>
          <div className="flex items-center gap-2">
            <div className="flex h-9 w-9 items-center justify-center rounded-xl bg-blue-600/20 text-blue-400 border border-blue-500/30">
              <Sliders className="h-5 w-5" />
            </div>
            <h2 className="text-xl font-extrabold text-white tracking-tight">Risk Policy &amp; Dynamic Threshold Simulator</h2>
          </div>
          <p className="mt-1 text-xs text-slate-400">
            Conduct live "what-if" risk analysis. Tune chargeback limits, ticket multipliers, and mule thresholds to measure GMV impact and dispute containment.
          </p>
        </div>

        <div className="flex items-center gap-3">
          <button
            onClick={() => {
              setCbThreshold(20)
              setTicketMultiplier(2.0)
              setMuleThreshold(2)
              setMinTxns(3)
            }}
            className="flex items-center gap-1.5 rounded-lg border border-[#2a3a5e] bg-[#161f33] px-3 py-1.5 text-xs text-slate-300 hover:bg-[#1e2a47] transition-all"
          >
            <RefreshCw className="h-3.5 w-3.5" />
            <span>Reset Defaults</span>
          </button>
        </div>
      </div>

      {/* Control Sliders Panel */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
        {/* Slider 1: Chargeback Cap */}
        <div className="rounded-xl border border-[#222f4c] bg-[#101626] p-4 space-y-2">
          <div className="flex items-center justify-between">
            <span className="text-xs font-semibold text-slate-300">Chargeback Threshold</span>
            <span className="rounded bg-blue-500/20 px-2 py-0.5 text-xs font-bold text-blue-400 font-mono">
              {cbThreshold}%
            </span>
          </div>
          <input
            type="range"
            min="5"
            max="50"
            step="1"
            value={cbThreshold}
            onChange={(e) => setCbThreshold(Number(e.target.value))}
            className="w-full h-1.5 bg-[#1e293b] rounded-lg appearance-none cursor-pointer accent-blue-500"
          />
          <div className="flex justify-between text-[10px] text-slate-500">
            <span>5% (Aggressive)</span>
            <span>20% (Default)</span>
            <span>50% (Lenient)</span>
          </div>
        </div>

        {/* Slider 2: Ticket Size Multiplier */}
        <div className="rounded-xl border border-[#222f4c] bg-[#101626] p-4 space-y-2">
          <div className="flex items-center justify-between">
            <span className="text-xs font-semibold text-slate-300">Ticket Size Multiplier</span>
            <span className="rounded bg-indigo-500/20 px-2 py-0.5 text-xs font-bold text-indigo-400 font-mono">
              {ticketMultiplier.toFixed(1)}x
            </span>
          </div>
          <input
            type="range"
            min="1.0"
            max="4.0"
            step="0.1"
            value={ticketMultiplier}
            onChange={(e) => setTicketMultiplier(Number(e.target.value))}
            className="w-full h-1.5 bg-[#1e293b] rounded-lg appearance-none cursor-pointer accent-indigo-500"
          />
          <div className="flex justify-between text-[10px] text-slate-500">
            <span>1.0x (Strict)</span>
            <span>2.0x (Default)</span>
            <span>4.0x (Relaxed)</span>
          </div>
        </div>

        {/* Slider 3: Mule Sharing Threshold */}
        <div className="rounded-xl border border-[#222f4c] bg-[#101626] p-4 space-y-2">
          <div className="flex items-center justify-between">
            <span className="text-xs font-semibold text-slate-300">Mule Account Sharing</span>
            <span className="rounded bg-amber-500/20 px-2 py-0.5 text-xs font-bold text-amber-400 font-mono">
              &ge; {muleThreshold} Merchants
            </span>
          </div>
          <input
            type="range"
            min="1"
            max="5"
            step="1"
            value={muleThreshold}
            onChange={(e) => setMuleThreshold(Number(e.target.value))}
            className="w-full h-1.5 bg-[#1e293b] rounded-lg appearance-none cursor-pointer accent-amber-500"
          />
          <div className="flex justify-between text-[10px] text-slate-500">
            <span>1 (All Accounts)</span>
            <span>2 (Shared Mules)</span>
            <span>5 (Syndicates)</span>
          </div>
        </div>

        {/* Slider 4: Evaluation Minimum Volume */}
        <div className="rounded-xl border border-[#222f4c] bg-[#101626] p-4 space-y-2">
          <div className="flex items-center justify-between">
            <span className="text-xs font-semibold text-slate-300">Min Evaluation Txns</span>
            <span className="rounded bg-emerald-500/20 px-2 py-0.5 text-xs font-bold text-emerald-400 font-mono">
              {minTxns} Txns
            </span>
          </div>
          <input
            type="range"
            min="1"
            max="10"
            step="1"
            value={minTxns}
            onChange={(e) => setMinTxns(Number(e.target.value))}
            className="w-full h-1.5 bg-[#1e293b] rounded-lg appearance-none cursor-pointer accent-emerald-500"
          />
          <div className="flex justify-between text-[10px] text-slate-500">
            <span>1 (Instant Flag)</span>
            <span>3 (Standard)</span>
            <span>10 (High Vol)</span>
          </div>
        </div>
      </div>

      {/* Real-Time Impact Metric Cards */}
      {simData && (
        <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
          <div className="rounded-xl border border-[#222f4c] bg-[#111726] p-5">
            <span className="text-xs text-slate-400 font-medium">Flagged Merchants</span>
            <div className="mt-2 flex items-baseline gap-2">
              <span className="text-2xl font-black text-white font-mono">
                {simData.simulated_metrics.flagged_merchants.toLocaleString()}
              </span>
              <span className={`text-xs font-bold px-1.5 py-0.5 rounded ${
                simData.delta_impact.net_merchants_flagged >= 0
                  ? 'bg-amber-500/20 text-amber-400'
                  : 'bg-emerald-500/20 text-emerald-400'
              }`}>
                {simData.delta_impact.net_merchants_flagged >= 0 ? '+' : ''}
                {simData.delta_impact.net_merchants_flagged} vs baseline
              </span>
            </div>
            <span className="text-[11px] text-slate-500 mt-1 block">Baseline: {simData.baseline_metrics.flagged_merchants}</span>
          </div>

          <div className="rounded-xl border border-[#222f4c] bg-[#111726] p-5">
            <span className="text-xs text-slate-400 font-medium">GMV at Risk Contained</span>
            <div className="mt-2 flex items-baseline gap-2">
              <span className="text-2xl font-black text-blue-400 font-mono">
                ₹{(simData.simulated_metrics.gmv_at_risk / 1e5).toFixed(1)}L
              </span>
              <span className="text-xs font-bold text-slate-400">
                ({simData.delta_impact.net_gmv_contained >= 0 ? '+' : ''}₹{(simData.delta_impact.net_gmv_contained / 1e5).toFixed(1)}L)
              </span>
            </div>
            <span className="text-[11px] text-slate-500 mt-1 block">Baseline: ₹{(simData.baseline_metrics.gmv_at_risk / 1e5).toFixed(1)}L</span>
          </div>

          <div className="rounded-xl border border-[#222f4c] bg-[#111726] p-5">
            <span className="text-xs text-slate-400 font-medium">Disputes Prevented</span>
            <div className="mt-2 flex items-baseline gap-2">
              <span className="text-2xl font-black text-emerald-400 font-mono">
                {simData.simulated_metrics.chargebacks_captured.toLocaleString()}
              </span>
              <span className="text-xs font-bold text-emerald-400">
                ({simData.delta_impact.net_disputes_prevented >= 0 ? '+' : ''}{simData.delta_impact.net_disputes_prevented})
              </span>
            </div>
            <span className="text-[11px] text-slate-500 mt-1 block">Dispute Vol: ₹{(simData.simulated_metrics.dispute_volume_contained / 1e5).toFixed(2)}L</span>
          </div>

          <div className="rounded-xl border border-[#222f4c] bg-[#111726] p-5">
            <span className="text-xs text-slate-400 font-medium">Platform Capture Rate</span>
            <div className="mt-2 flex items-baseline gap-2">
              <span className="text-2xl font-black text-purple-400 font-mono">
                {simData.simulated_metrics.platform_capture_rate_pct}%
              </span>
              <span className="text-xs text-purple-300 font-medium">of total disputes</span>
            </div>
            <span className="text-[11px] text-slate-500 mt-1 block">Interception efficiency</span>
          </div>
        </div>
      )}

      {/* Chart & Recommendation */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        <div className="lg:col-span-2 rounded-2xl border border-[#222f4c] bg-[#101626] p-6 space-y-4">
          <div className="flex items-center justify-between">
            <h3 className="text-sm font-bold text-white">Policy Impact Comparison (Baseline vs Simulated)</h3>
            <span className="text-xs text-slate-400">Grounded in 4,343 merchants &amp; 20,000 transactions</span>
          </div>
          <div className="h-64 w-full">
            <ResponsiveContainer width="100%" height="100%">
              <BarChart data={chartData} margin={{ top: 20, right: 30, left: 20, bottom: 5 }}>
                <CartesianGrid strokeDasharray="3 3" stroke="#1e293b" vertical={false} />
                <XAxis dataKey="metric" stroke="#64748b" tick={{ fill: '#94a3b8', fontSize: 12 }} />
                <YAxis stroke="#64748b" tick={{ fill: '#94a3b8', fontSize: 12 }} />
                <Tooltip 
                  contentStyle={{ backgroundColor: '#0f172a', borderColor: '#334155', borderRadius: '8px', fontSize: '12px' }}
                />
                <Legend wrapperStyle={{ fontSize: '12px', paddingTop: '10px' }} />
                <Bar dataKey="Baseline" fill="#475569" radius={[4, 4, 0, 0]} />
                <Bar dataKey="Simulated" fill="#3b82f6" radius={[4, 4, 0, 0]} />
              </BarChart>
            </ResponsiveContainer>
          </div>
        </div>

        {/* Executive Recommendation Box */}
        <div className="rounded-2xl border border-blue-500/20 bg-gradient-to-br from-[#121a30] to-[#0c1222] p-6 flex flex-col justify-between">
          <div className="space-y-3">
            <div className="flex items-center gap-2 text-blue-400 font-bold text-xs uppercase tracking-wider">
              <Zap className="h-4 w-4" />
              <span>Policy Optimization Advisory</span>
            </div>
            <h4 className="text-base font-extrabold text-white">Executive Strategy Verdict</h4>
            <p className="text-xs text-slate-300 leading-relaxed">
              {simData?.recommendation || 'Calculating policy threshold recommendation...'}
            </p>
          </div>

          <div className="mt-6 pt-4 border-t border-[#222f4c] text-[11px] text-slate-400 flex items-center gap-2">
            <Info className="h-4 w-4 text-blue-400 shrink-0" />
            <span>Simulated thresholds can be directly deployed to transaction-scoring rule engines.</span>
          </div>
        </div>
      </div>

      {/* Incremental Flagged Merchants Table */}
      {simData && simData.incremental_flagged_sample && simData.incremental_flagged_sample.length > 0 && (
        <div className="rounded-2xl border border-[#222f4c] bg-[#101626] overflow-hidden">
          <div className="border-b border-[#222f4c] p-5 flex items-center justify-between bg-[#131b2e]">
            <div>
              <h3 className="text-sm font-bold text-white">
                Incremental Merchants Triggered Under Simulated Policy ({simData.incremental_flagged_sample.length})
              </h3>
              <p className="text-xs text-slate-400 mt-0.5">
                Merchants passing baseline filters but newly flagged under the adjusted risk parameters.
              </p>
            </div>
          </div>

          <div className="overflow-x-auto">
            <table className="w-full text-left text-xs">
              <thead className="bg-[#0b101c] text-slate-400 uppercase tracking-wider text-[10px] border-b border-[#222f4c]">
                <tr>
                  <th className="px-5 py-3 font-semibold">Merchant ID / Trade Name</th>
                  <th className="px-4 py-3 font-semibold">Category</th>
                  <th className="px-4 py-3 font-semibold">Volume (INR)</th>
                  <th className="px-4 py-3 font-semibold">Dispute Rate</th>
                  <th className="px-4 py-3 font-semibold">Ticket Deviation</th>
                  <th className="px-4 py-3 font-semibold">Mule Count</th>
                  <th className="px-4 py-3 font-semibold text-right">Forensic Action</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-[#1e293b] text-slate-200">
                {simData.incremental_flagged_sample.map((m: any) => (
                  <tr key={m.merchant_id} className="hover:bg-[#161f33] transition-colors">
                    <td className="px-5 py-3">
                      <div className="font-semibold text-white">{m.merchant_name}</div>
                      <div className="font-mono text-[11px] text-blue-400">{m.merchant_id}</div>
                    </td>
                    <td className="px-4 py-3 text-slate-300">{m.merchant_category}</td>
                    <td className="px-4 py-3 font-mono font-medium">₹{m.total_volume.toLocaleString()}</td>
                    <td className="px-4 py-3">
                      <span className={`px-2 py-0.5 rounded font-mono font-bold text-[11px] ${
                        m.cb_rate_pct >= cbThreshold ? 'bg-red-500/20 text-red-400 border border-red-500/30' : 'text-slate-300'
                      }`}>
                        {m.cb_rate_pct}%
                      </span>
                    </td>
                    <td className="px-4 py-3 font-mono">
                      <span className={m.ticket_deviation_ratio >= ticketMultiplier ? 'text-amber-400 font-bold' : 'text-slate-300'}>
                        {m.ticket_deviation_ratio}x
                      </span>
                    </td>
                    <td className="px-4 py-3 font-mono">
                      {m.shared_acc_count > 1 ? (
                        <span className="text-purple-400 font-bold">{m.shared_acc_count} stores</span>
                      ) : (
                        <span className="text-slate-500">1</span>
                      )}
                    </td>
                    <td className="px-4 py-3 text-right">
                      <button
                        onClick={() => handleOpenSTR(m.merchant_id)}
                        className="inline-flex items-center gap-1.5 rounded-lg bg-red-600/20 border border-red-500/30 px-2.5 py-1 text-[11px] font-semibold text-red-400 hover:bg-red-600/30 transition-all"
                      >
                        <FileText className="h-3 w-3" />
                        <span>Generate STR</span>
                      </button>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      )}

      {/* STR Report Modal */}
      <STRReportModal
        isOpen={!!selectedMchForStr}
        onClose={() => setSelectedMchForStr(null)}
        reportData={strReportData}
        isLoading={isStrLoading}
      />
    </div>
  )
}
