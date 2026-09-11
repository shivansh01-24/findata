import React, { useEffect, useState } from 'react'
import { 
  TrendingUp, 
  AlertOctagon, 
  CheckCircle2, 
  XCircle, 
  Clock, 
  ArrowUpRight, 
  ShieldAlert, 
  DollarSign, 
  CreditCard, 
  Layers 
} from 'lucide-react'
import { 
  ResponsiveContainer, 
  AreaChart, 
  Area, 
  XAxis, 
  YAxis, 
  Tooltip, 
  BarChart, 
  Bar, 
  Cell, 
  PieChart, 
  Pie 
} from 'recharts'

export const ExecutiveOverview: React.FC = () => {
  const [data, setData] = useState<any>(null)
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    fetch('/api/analytics/overview')
      .then(res => res.json())
      .then(d => {
        setData(d)
        setLoading(false)
      })
      .catch(err => {
        console.error('Error fetching overview:', err)
        setLoading(false)
      })
  }, [])

  if (loading) {
    return (
      <div className="flex h-96 items-center justify-center">
        <div className="flex flex-col items-center gap-3">
          <div className="h-8 w-8 animate-spin rounded-full border-2 border-blue-500 border-t-transparent"></div>
          <p className="text-xs text-slate-400">Loading Trusted Analytics Telemetry...</p>
        </div>
      </div>
    )
  }

  if (!data) {
    return <div className="p-8 text-center text-slate-400">Failed to load analytics data.</div>
  }

  const k = data.kpis

  return (
    <div className="space-y-6">
      {/* Benchmark Question Spotlight Banner */}
      <div className="relative overflow-hidden rounded-2xl border border-blue-500/30 bg-gradient-to-r from-blue-900/30 via-indigo-900/20 to-purple-900/30 p-5 backdrop-blur-md shadow-xl">
        <div className="flex flex-col md:flex-row items-start md:items-center justify-between gap-4">
          <div className="flex items-center gap-4">
            <div className="flex h-12 w-12 items-center justify-center rounded-2xl bg-blue-600/30 text-blue-400 border border-blue-500/40 shadow-inner">
              <ShieldAlert className="h-7 w-7" />
            </div>
            <div>
              <div className="flex items-center gap-2">
                <span className="text-xs font-bold uppercase tracking-wider text-blue-400">Key Datathon Finding</span>
                <span className="rounded bg-red-500/20 px-2 py-0.5 text-[10px] font-bold text-red-400 border border-red-500/30">CRITICAL RATIO</span>
              </div>
              <h2 className="text-lg font-bold text-white mt-0.5">
                Highest Chargeback-to-Transaction Ratio: <span className="text-amber-400">Apparel (30.34%)</span> &amp; <span className="text-amber-400">Misc Retail (18.87%)</span>
              </h2>
              <p className="text-xs text-slate-300 mt-1">
                Grounded on 20,000 trusted UPI transactions and 2,800 validated chargebacks across Q1 2026.
              </p>
            </div>
          </div>
          <div className="flex items-center gap-3">
            <div className="rounded-xl border border-[#222f4c] bg-[#111726]/80 px-4 py-2 text-right">
              <span className="block text-[11px] text-slate-400">Dispute Ratio</span>
              <span className="text-base font-extrabold text-amber-400 mono">30.34%</span>
            </div>
            <div className="rounded-xl border border-[#222f4c] bg-[#111726]/80 px-4 py-2 text-right">
              <span className="block text-[11px] text-slate-400">Platform Avg</span>
              <span className="text-base font-extrabold text-blue-400 mono">14.00%</span>
            </div>
          </div>
        </div>
      </div>

      {/* KPI Cards Grid */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
        {/* Card 1: Gross Volume */}
        <div className="rounded-2xl border border-[#222f4c] bg-[#111726] p-5 shadow-lg relative overflow-hidden group hover:border-blue-500/40 transition-colors">
          <div className="flex items-center justify-between">
            <span className="text-xs font-semibold text-slate-400 uppercase tracking-wider">Gross UPI Volume</span>
            <div className="rounded-xl bg-blue-500/10 p-2 text-blue-400 border border-blue-500/20">
              <DollarSign className="h-5 w-5" />
            </div>
          </div>
          <div className="mt-3">
            <h3 className="text-2xl font-black text-white mono">₹{(k.total_volume / 1e6).toFixed(2)}M</h3>
            <div className="flex items-center gap-2 mt-1.5 text-xs text-slate-400">
              <span className="text-emerald-400 font-semibold flex items-center">
                <ArrowUpRight className="h-3.5 w-3.5 mr-0.5" /> 20,000
              </span>
              <span>total processed transactions</span>
            </div>
          </div>
        </div>

        {/* Card 2: Success vs Failure */}
        <div className="rounded-2xl border border-[#222f4c] bg-[#111726] p-5 shadow-lg relative overflow-hidden group hover:border-blue-500/40 transition-colors">
          <div className="flex items-center justify-between">
            <span className="text-xs font-semibold text-slate-400 uppercase tracking-wider">Success Rate</span>
            <div className="rounded-xl bg-emerald-500/10 p-2 text-emerald-400 border border-emerald-500/20">
              <CheckCircle2 className="h-5 w-5" />
            </div>
          </div>
          <div className="mt-3">
            <h3 className="text-2xl font-black text-emerald-400 mono">{k.success_rate_pct}%</h3>
            <div className="flex items-center gap-2 mt-1.5 text-xs text-slate-400">
              <span className="text-red-400 font-semibold flex items-center">
                <XCircle className="h-3.5 w-3.5 mr-0.5" /> {k.failure_rate_pct}%
              </span>
              <span>failed ({k.failed_transactions.toLocaleString()})</span>
            </div>
          </div>
        </div>

        {/* Card 3: Chargeback Exposure */}
        <div className="rounded-2xl border border-[#222f4c] bg-[#111726] p-5 shadow-lg relative overflow-hidden group hover:border-blue-500/40 transition-colors">
          <div className="flex items-center justify-between">
            <span className="text-xs font-semibold text-slate-400 uppercase tracking-wider">Disputed Volume</span>
            <div className="rounded-xl bg-amber-500/10 p-2 text-amber-400 border border-amber-500/20">
              <AlertOctagon className="h-5 w-5" />
            </div>
          </div>
          <div className="mt-3">
            <h3 className="text-2xl font-black text-amber-400 mono">₹{(k.total_disputed_volume / 1e6).toFixed(2)}M</h3>
            <div className="flex items-center gap-2 mt-1.5 text-xs text-slate-400">
              <span className="text-amber-400 font-semibold">
                {k.total_chargebacks.toLocaleString()}
              </span>
              <span>chargebacks logged ({k.chargeback_ratio_pct}%)</span>
            </div>
          </div>
        </div>

        {/* Card 4: Dispute Reporting Latency */}
        <div className="rounded-2xl border border-[#222f4c] bg-[#111726] p-5 shadow-lg relative overflow-hidden group hover:border-blue-500/40 transition-colors">
          <div className="flex items-center justify-between">
            <span className="text-xs font-semibold text-slate-400 uppercase tracking-wider">Avg Dispute Delay</span>
            <div className="rounded-xl bg-purple-500/10 p-2 text-purple-400 border border-purple-500/20">
              <Clock className="h-5 w-5" />
            </div>
          </div>
          <div className="mt-3">
            <h3 className="text-2xl font-black text-purple-400 mono">{k.avg_reporting_delay_days} Days</h3>
            <div className="flex items-center gap-2 mt-1.5 text-xs text-slate-400">
              <span className="text-slate-300 font-semibold">Avg Ticket</span>
              <span>₹{k.avg_ticket_size.toLocaleString()}</span>
            </div>
          </div>
        </div>
      </div>

      {/* Row 2: Charts (Daily Trend & Category Ratio Benchmark) */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Daily Transaction Volume Chart */}
        <div className="rounded-2xl border border-[#222f4c] bg-[#111726] p-6 shadow-xl">
          <div className="flex items-center justify-between mb-4">
            <div>
              <h3 className="text-base font-bold text-white">Daily Transaction Volume &amp; Velocity</h3>
              <p className="text-xs text-slate-400">Transaction amounts processed across Q1 2026</p>
            </div>
            <span className="rounded-lg bg-blue-500/10 px-2.5 py-1 text-xs font-semibold text-blue-400 border border-blue-500/20">
              Q1 2026
            </span>
          </div>
          <div className="h-72 w-full">
            <ResponsiveContainer width="100%" height="100%">
              <AreaChart data={data.daily_trends} margin={{ top: 10, right: 10, left: -20, bottom: 0 }}>
                <defs>
                  <linearGradient id="colorVol" x1="0" y1="0" x2="0" y2="1">
                    <stop offset="5%" stopColor="#3b82f6" stopOpacity={0.4}/>
                    <stop offset="95%" stopColor="#3b82f6" stopOpacity={0}/>
                  </linearGradient>
                </defs>
                <XAxis 
                  dataKey="txn_date" 
                  stroke="#64748b" 
                  fontSize={11} 
                  tickLine={false}
                  tickFormatter={(val) => val ? val.slice(5) : ''}
                />
                <YAxis 
                  stroke="#64748b" 
                  fontSize={11} 
                  tickLine={false}
                  tickFormatter={(val) => `₹${(val / 1e6).toFixed(1)}M`}
                />
                <Tooltip 
                  contentStyle={{ backgroundColor: '#161f33', borderColor: '#222f4c', borderRadius: '12px', fontSize: '12px' }}
                  formatter={(val: any) => [`₹${Number(val).toLocaleString()}`, 'Volume']}
                  labelFormatter={(lbl) => `Date: ${lbl}`}
                />
                <Area type="monotone" dataKey="volume" stroke="#3b82f6" strokeWidth={2} fillOpacity={1} fill="url(#colorVol)" />
              </AreaChart>
            </ResponsiveContainer>
          </div>
        </div>

        {/* Category Chargeback Ratio Comparison */}
        <div className="rounded-2xl border border-[#222f4c] bg-[#111726] p-6 shadow-xl">
          <div className="flex items-center justify-between mb-4">
            <div>
              <h3 className="text-base font-bold text-white">Dispute Ratio by Merchant Category</h3>
              <p className="text-xs text-slate-400">Chargeback-to-Transaction Ratio (%) per Category</p>
            </div>
            <span className="rounded-lg bg-amber-500/10 px-2.5 py-1 text-xs font-semibold text-amber-400 border border-amber-500/20">
              Benchmark
            </span>
          </div>
          <div className="h-72 w-full">
            <ResponsiveContainer width="100%" height="100%">
              <BarChart data={data.category_ratios} layout="vertical" margin={{ top: 5, right: 30, left: 40, bottom: 5 }}>
                <XAxis type="number" stroke="#64748b" fontSize={11} tickFormatter={(v) => `${v}%`} />
                <YAxis dataKey="category" type="category" stroke="#cbd5e1" fontSize={11} tickLine={false} width={100} />
                <Tooltip 
                  contentStyle={{ backgroundColor: '#161f33', borderColor: '#222f4c', borderRadius: '12px', fontSize: '12px' }}
                  formatter={(val: any, name: any, item: any) => [
                    `${val}% (${item.payload.chargeback_count} disputes / ${item.payload.transaction_count.toLocaleString()} txns)`,
                    'Dispute Ratio'
                  ]}
                />
                <Bar dataKey="chargeback_to_transaction_ratio_pct" radius={[0, 6, 6, 0]}>
                  {data.category_ratios.map((entry: any, index: number) => (
                    <Cell 
                      key={`cell-${index}`} 
                      fill={entry.chargeback_to_transaction_ratio_pct > 20 ? '#ef4444' : entry.chargeback_to_transaction_ratio_pct > 13 ? '#f59e0b' : '#3b82f6'} 
                    />
                  ))}
                </Bar>
              </BarChart>
            </ResponsiveContainer>
          </div>
        </div>
      </div>

      {/* Row 3: Breakdown Grids (Reasons, Severity, Channels) */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
        {/* Chargeback Reason Breakdown */}
        <div className="rounded-2xl border border-[#222f4c] bg-[#111726] p-5 shadow-lg">
          <h4 className="text-sm font-bold text-white mb-1">Dispute Reasons</h4>
          <p className="text-xs text-slate-400 mb-3">Dominant dispute classifications</p>
          <div className="space-y-2.5">
            {data.reasons.map((r: any) => (
              <div key={r.reason_category} className="rounded-xl border border-[#222f4c] bg-[#161f33] p-2.5">
                <div className="flex items-center justify-between text-xs mb-1">
                  <span className="font-semibold text-slate-200">{r.reason_category}</span>
                  <span className="font-bold text-blue-400 mono">{r.percentage}%</span>
                </div>
                <div className="h-1.5 w-full rounded-full bg-[#0a0d14] overflow-hidden">
                  <div className="h-full bg-blue-500 rounded-full" style={{ width: `${r.percentage}%` }}></div>
                </div>
                <div className="flex justify-between text-[11px] text-slate-400 mt-1">
                  <span>{r.count.toLocaleString()} disputes</span>
                  <span>₹{(r.volume / 1e6).toFixed(2)}M</span>
                </div>
              </div>
            ))}
          </div>
        </div>

        {/* Severity Breakdown */}
        <div className="rounded-2xl border border-[#222f4c] bg-[#111726] p-5 shadow-lg">
          <h4 className="text-sm font-bold text-white mb-1">Dispute Severity</h4>
          <p className="text-xs text-slate-400 mb-3">Investigation escalation levels</p>
          <div className="space-y-2.5">
            {data.severities.map((s: any) => {
              const color = s.severity === 'Critical' ? 'text-red-400 bg-red-500/10 border-red-500/30' :
                            s.severity === 'High' ? 'text-amber-400 bg-amber-500/10 border-amber-500/30' :
                            s.severity === 'Medium' ? 'text-blue-400 bg-blue-500/10 border-blue-500/30' :
                            'text-slate-400 bg-slate-500/10 border-slate-500/30'
              return (
                <div key={s.severity} className="flex items-center justify-between rounded-xl border border-[#222f4c] bg-[#161f33] p-3">
                  <div className="flex items-center gap-2.5">
                    <span className={`px-2 py-0.5 rounded text-xs font-bold border ${color}`}>
                      {s.severity}
                    </span>
                    <span className="text-xs text-slate-300">{s.count.toLocaleString()} cases</span>
                  </div>
                  <span className="text-xs font-bold text-white mono">{s.percentage}%</span>
                </div>
              )
            })}
          </div>
        </div>

        {/* Channel Breakdown */}
        <div className="rounded-2xl border border-[#222f4c] bg-[#111726] p-5 shadow-lg">
          <h4 className="text-sm font-bold text-white mb-1">Intake Channels</h4>
          <p className="text-xs text-slate-400 mb-3">Customer reporting origination</p>
          <div className="space-y-2.5">
            {data.channels.map((c: any) => (
              <div key={c.channel} className="flex items-center justify-between rounded-xl border border-[#222f4c] bg-[#161f33] p-3">
                <span className="text-xs font-semibold text-slate-200">{c.channel}</span>
                <div className="flex items-center gap-3">
                  <span className="text-xs text-slate-400">{c.count.toLocaleString()}</span>
                  <span className="text-xs font-bold text-indigo-400 mono">{c.percentage}%</span>
                </div>
              </div>
            ))}
          </div>
        </div>
      </div>
    </div>
  )
}
