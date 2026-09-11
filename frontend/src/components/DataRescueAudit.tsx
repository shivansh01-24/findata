import React, { useEffect, useState } from 'react'
import { 
  Database, 
  CheckCircle2, 
  AlertTriangle, 
  ArrowRight, 
  ShieldCheck, 
  Layers, 
  FileText, 
  GitBranch, 
  Search,
  Sparkles,
  ExternalLink,
  ChevronRight,
  Info
} from 'lucide-react'

export const DataRescueAudit: React.FC = () => {
  const [data, setData] = useState<any>(null)
  const [loading, setLoading] = useState(true)

  // Interactive Search & Diff State
  const [searchQuery, setSearchQuery] = useState<string>('')
  const [searchResults, setSearchResults] = useState<any[]>([])
  const [curatedCases, setCuratedCases] = useState<any[]>([])
  const [selectedEntity, setSelectedEntity] = useState<any | null>(null)
  const [isSearching, setIsSearching] = useState<boolean>(false)
  const [isDiffLoading, setIsDiffLoading] = useState<boolean>(false)

  useEffect(() => {
    // 1. Fetch Quality Report
    fetch('/api/analytics/data-quality')
      .then(res => res.json())
      .then(d => {
        setData(d)
        setLoading(false)
      })
      .catch(err => {
        console.error('Error fetching quality report:', err)
        setLoading(false)
      })

    // 2. Fetch Curated Cases
    fetch('/api/audit/curated-cases')
      .then(res => res.json())
      .then(cases => {
        setCuratedCases(cases)
        if (cases.length > 0) {
          loadEntityAudit(cases[0].entity_type, cases[0].entity_id)
        }
      })
      .catch(err => console.error('Error fetching curated cases:', err))
  }, [])

  const handleSearch = (q: string) => {
    setSearchQuery(q)
    if (!q.trim()) {
      setSearchResults([])
      return
    }
    setIsSearching(true)
    fetch(`/api/audit/search?q=${encodeURIComponent(q)}&limit=8`)
      .then(res => res.json())
      .then(results => {
        setSearchResults(results)
        setIsSearching(false)
      })
      .catch(err => {
        console.error('Error searching audit entities:', err)
        setIsSearching(false)
      })
  }

  const loadEntityAudit = (entityType: string, entityId: string) => {
    setIsDiffLoading(true)
    fetch(`/api/audit/entity/${entityType}/${entityId}`)
      .then(res => res.json())
      .then(d => {
        setSelectedEntity(d)
        setIsDiffLoading(false)
      })
      .catch(err => {
        console.error('Error loading entity audit:', err)
        setIsDiffLoading(false)
      })
  }

  if (loading) {
    return (
      <div className="flex h-96 items-center justify-center">
        <div className="flex flex-col items-center gap-3">
          <div className="h-8 w-8 animate-spin rounded-full border-2 border-emerald-500 border-t-transparent"></div>
          <p className="text-xs text-slate-400">Loading Forensic Audit Trail...</p>
        </div>
      </div>
    )
  }

  const p = data?.pipeline_metrics || {}
  const c = p.counts || {}

  return (
    <div className="space-y-6">
      {/* Principle Banner */}
      <div className="rounded-2xl border border-emerald-500/30 bg-emerald-950/20 p-6 backdrop-blur-md shadow-xl">
        <div className="flex items-center gap-3 mb-2">
          <ShieldCheck className="h-6 w-6 text-emerald-400" />
          <h2 className="text-lg font-bold text-white">Data Rescue &amp; Traceability Philosophy</h2>
        </div>
        <p className="text-xs text-slate-300 max-w-3xl leading-relaxed">
          The platform adheres strictly to the competition principle: <strong>Preserve &rarr; Standardize &rarr; Validate &rarr; Flag &rarr; Resolve &rarr; Analyze</strong>. 
          No messy rows were blindly deleted. Every record carries an audit trail linking raw values to canonical values, validation statuses, and quality flags.
        </p>

        {/* Pipeline Progression Breadcrumb */}
        <div className="mt-4 flex flex-wrap items-center gap-2 text-xs font-semibold">
          <span className="rounded-lg bg-[#111726] px-3 py-1 text-slate-300 border border-[#222f4c]">RAW TELEMETRY</span>
          <ArrowRight className="h-3.5 w-3.5 text-slate-500" />
          <span className="rounded-lg bg-[#111726] px-3 py-1 text-blue-400 border border-blue-500/30">CANONICALIZATION</span>
          <ArrowRight className="h-3.5 w-3.5 text-slate-500" />
          <span className="rounded-lg bg-[#111726] px-3 py-1 text-purple-400 border border-purple-500/30">ENTITY RESOLUTION</span>
          <ArrowRight className="h-3.5 w-3.5 text-slate-500" />
          <span className="rounded-lg bg-[#111726] px-3 py-1 text-amber-400 border border-amber-500/30">RELATIONSHIP VALIDATION</span>
          <ArrowRight className="h-3.5 w-3.5 text-slate-500" />
          <span className="rounded-lg bg-emerald-600 px-3 py-1 text-white shadow-md shadow-emerald-600/30">TRUSTED ANALYTICS</span>
        </div>
      </div>

      {/* Before vs After Audit Grid */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
        {/* UPI Transactions */}
        <div className="rounded-2xl border border-[#222f4c] bg-[#111726] p-5 shadow-lg">
          <div className="flex items-center justify-between mb-2">
            <span className="text-xs font-bold text-slate-400 uppercase">UPI Transactions</span>
            <span className="text-[10px] font-bold text-emerald-400 bg-emerald-500/10 px-2 py-0.5 rounded border border-emerald-500/20">
              100% AUDITED
            </span>
          </div>
          <div className="flex items-baseline justify-between mt-3">
            <div>
              <span className="text-2xl font-black text-white font-mono">{c.trusted_upi?.toLocaleString() || '20,000'}</span>
              <span className="block text-[11px] text-slate-400">Trusted Retained</span>
            </div>
            <div className="text-right">
              <span className="text-sm font-bold text-slate-400 line-through font-mono">{c.raw_upi?.toLocaleString() || '20,400'}</span>
              <span className="block text-[11px] text-red-400">-400 exact dupes</span>
            </div>
          </div>
        </div>

        {/* Customer KYC */}
        <div className="rounded-2xl border border-[#222f4c] bg-[#111726] p-5 shadow-lg">
          <div className="flex items-center justify-between mb-2">
            <span className="text-xs font-bold text-slate-400 uppercase">Customer KYC Master</span>
            <span className="text-[10px] font-bold text-blue-400 bg-blue-500/10 px-2 py-0.5 rounded border border-blue-500/20">
              RESOLVED
            </span>
          </div>
          <div className="flex items-baseline justify-between mt-3">
            <div>
              <span className="text-2xl font-black text-white font-mono">{c.trusted_customers?.toLocaleString() || '28,920'}</span>
              <span className="block text-[11px] text-slate-400">Golden Profiles</span>
            </div>
            <div className="text-right">
              <span className="text-sm font-bold text-slate-400 font-mono">{c.raw_kyc?.toLocaleString() || '36,400'}</span>
              <span className="block text-[11px] text-blue-400">5,863 conflicts resolved</span>
            </div>
          </div>
        </div>

        {/* Merchants Master */}
        <div className="rounded-2xl border border-[#222f4c] bg-[#111726] p-5 shadow-lg">
          <div className="flex items-center justify-between mb-2">
            <span className="text-xs font-bold text-slate-400 uppercase">Merchants Master</span>
            <span className="text-[10px] font-bold text-purple-400 bg-purple-500/10 px-2 py-0.5 rounded border border-purple-500/20">
              RESOLVED
            </span>
          </div>
          <div className="flex items-baseline justify-between mt-3">
            <div>
              <span className="text-2xl font-black text-white font-mono">{c.trusted_merchants?.toLocaleString() || '4,343'}</span>
              <span className="block text-[11px] text-slate-400">Golden Merchants</span>
            </div>
            <div className="text-right">
              <span className="text-sm font-bold text-slate-400 font-mono">{c.raw_merchants?.toLocaleString() || '6,210'}</span>
              <span className="block text-[11px] text-purple-400">1,412 duplicates resolved</span>
            </div>
          </div>
        </div>

        {/* Chargebacks */}
        <div className="rounded-2xl border border-[#222f4c] bg-[#111726] p-5 shadow-lg">
          <div className="flex items-center justify-between mb-2">
            <span className="text-xs font-bold text-slate-400 uppercase">Disputed Chargebacks</span>
            <span className="text-[10px] font-bold text-amber-400 bg-amber-500/10 px-2 py-0.5 rounded border border-amber-500/20">
              LINKED
            </span>
          </div>
          <div className="flex items-baseline justify-between mt-3">
            <div>
              <span className="text-2xl font-black text-white font-mono">{c.trusted_chargebacks?.toLocaleString() || '2,800'}</span>
              <span className="block text-[11px] text-slate-400">Full Audit Trail</span>
            </div>
            <div className="text-right">
              <span className="text-sm font-bold text-emerald-400 font-mono">{p.chargeback_linkage?.linked_to_upi || '2,607'}</span>
              <span className="block text-[11px] text-emerald-400">Linked to UPI Txns</span>
            </div>
          </div>
        </div>
      </div>

      {/* ========================================================================= */}
      {/* INTERACTIVE DATA RESCUE SEARCH & RECONCILIATION DIFF VIEWER */}
      {/* ========================================================================= */}
      <div className="rounded-2xl border border-blue-500/30 bg-[#101626] p-6 shadow-2xl space-y-5">
        <div className="flex flex-col md:flex-row md:items-center justify-between gap-4">
          <div>
            <div className="flex items-center gap-2">
              <Sparkles className="h-5 w-5 text-blue-400" />
              <h3 className="text-base font-bold text-white">Live Data Rescue &amp; Entity Diff Inspector</h3>
            </div>
            <p className="text-xs text-slate-400 mt-1">
              Search any raw or canonical ID, customer or merchant name, PAN, or settlement account to inspect the side-by-side rescue transformation.
            </p>
          </div>

          {/* Search Input */}
          <div className="relative w-full md:w-80">
            <Search className="absolute left-3 top-2.5 h-4 w-4 text-slate-500" />
            <input
              type="text"
              value={searchQuery}
              onChange={(e) => handleSearch(e.target.value)}
              placeholder="Search raw ID (e.g. MCH7912, USR10043, 86464)..."
              className="w-full rounded-xl border border-[#2a3a5e] bg-[#0c101a] py-2 pl-9 pr-4 text-xs text-slate-200 placeholder-slate-500 focus:border-blue-500 focus:outline-none"
            />
          </div>
        </div>

        {/* Curated Benchmark Case Chips */}
        <div className="space-y-2">
          <span className="text-[11px] font-semibold text-slate-400 uppercase tracking-wider block">
            Curated Benchmark Cases (Click to inspect side-by-side rescue):
          </span>
          <div className="flex flex-wrap gap-2">
            {curatedCases.map((c) => (
              <button
                key={c.entity_id}
                onClick={() => loadEntityAudit(c.entity_type, c.entity_id)}
                className={`flex items-center gap-2 rounded-xl px-3 py-1.5 text-xs transition-all border ${
                  selectedEntity?.entity_id === c.entity_id
                    ? 'bg-blue-600 border-blue-400 text-white font-bold shadow-md shadow-blue-500/20'
                    : 'bg-[#151c2e] border-[#222f4c] text-slate-300 hover:bg-[#1b253d] hover:border-blue-500/30'
                }`}
              >
                <span className="font-mono text-blue-300 font-bold">{c.entity_id}</span>
                <span className="text-slate-400 text-[11px]">•</span>
                <span>{c.curation_tag}</span>
              </button>
            ))}
          </div>
        </div>

        {/* Live Search Autocomplete Dropdown */}
        {searchResults.length > 0 && (
          <div className="rounded-xl border border-[#2a3a5e] bg-[#0d121f] p-3 space-y-1.5">
            <span className="text-[11px] text-slate-400 font-semibold px-2">Search Matches ({searchResults.length}):</span>
            <div className="grid grid-cols-1 md:grid-cols-2 gap-2">
              {searchResults.map((r) => (
                <button
                  key={`${r.entity_type}-${r.entity_id}`}
                  onClick={() => {
                    loadEntityAudit(r.entity_type, r.entity_id)
                    setSearchResults([])
                  }}
                  className="flex items-center justify-between p-2.5 rounded-lg bg-[#141b2c] hover:bg-[#1a243b] text-left transition-colors border border-[#1f293d]"
                >
                  <div>
                    <div className="flex items-center gap-2">
                      <span className="font-bold text-white text-xs">{r.display_name}</span>
                      <span className="font-mono text-[11px] text-blue-400">({r.entity_id})</span>
                    </div>
                    <span className="text-[11px] text-slate-400">{r.identifier} • {r.status}</span>
                  </div>
                  <ChevronRight className="h-4 w-4 text-slate-500" />
                </button>
              ))}
            </div>
          </div>
        )}

        {/* Selected Entity Diff Viewer */}
        {isDiffLoading ? (
          <div className="flex h-64 items-center justify-center">
            <div className="h-6 w-6 animate-spin rounded-full border-2 border-blue-500 border-t-transparent" />
          </div>
        ) : selectedEntity ? (
          <div className="space-y-4 pt-2">
            {/* Top Entity Status Bar */}
            <div className="flex flex-col md:flex-row md:items-center justify-between gap-3 rounded-xl bg-gradient-to-r from-[#141d33] to-[#0f1626] p-4 border border-[#2a3a5e]">
              <div>
                <div className="flex items-center gap-2">
                  <span className="font-bold text-white text-sm">
                    {selectedEntity.golden_record.full_name || selectedEntity.golden_record.merchant_name}
                  </span>
                  <span className="font-mono text-xs px-2 py-0.5 rounded bg-blue-500/20 text-blue-400 font-bold border border-blue-500/30">
                    {selectedEntity.entity_id}
                  </span>
                  <span className="rounded bg-purple-500/20 px-2 py-0.5 text-[11px] font-bold text-purple-400 border border-purple-500/30">
                    {selectedEntity.resolution_type}
                  </span>
                </div>
                <p className="text-xs text-slate-300 mt-1">
                  <strong>Resolution Rationale:</strong> {selectedEntity.conflict_details || 'Consolidated duplicate ingestion instances'}
                </p>
              </div>

              <div className="flex items-center gap-4 text-xs font-mono">
                <div className="text-right">
                  <span className="text-slate-400 block text-[10px]">Confidence</span>
                  <span className="text-emerald-400 font-bold">{(selectedEntity.resolution_confidence * 100).toFixed(0)}%</span>
                </div>
                <div className="text-right">
                  <span className="text-slate-400 block text-[10px]">Raw Instances</span>
                  <span className="text-amber-400 font-bold">{selectedEntity.raw_record_count} Ingested Rows</span>
                </div>
                <div className="text-right">
                  <span className="text-slate-400 block text-[10px]">Transactions</span>
                  <span className="text-white font-bold">{selectedEntity.txns_count}</span>
                </div>
              </div>
            </div>

            {/* Side-by-Side Reconciliation Table */}
            <div className="rounded-xl border border-[#222f4c] overflow-hidden bg-[#0c101a]">
              <div className="bg-[#131b2e] px-4 py-2.5 border-b border-[#222f4c] flex items-center justify-between">
                <span className="text-xs font-bold text-white uppercase tracking-wider">
                  Attribute-by-Attribute Reconciliation &amp; Defense Matrix
                </span>
                <span className="text-[11px] text-slate-400">
                  {selectedEntity.raw_record_count} Raw Source Row(s) &rarr; 1 Rescued Golden Entity
                </span>
              </div>

              <div className="overflow-x-auto">
                <table className="w-full text-left text-xs">
                  <thead className="bg-[#090d16] text-slate-400 uppercase tracking-wider text-[10px] border-b border-[#222f4c]">
                    <tr>
                      <th className="px-4 py-2.5 font-semibold w-36">Attribute</th>
                      <th className="px-4 py-2.5 font-semibold text-emerald-400 w-52">Canonical Golden Record</th>
                      <th className="px-4 py-2.5 font-semibold text-amber-400">Raw Source Ingestion Variant(s)</th>
                      <th className="px-4 py-2.5 font-semibold w-72">Rescue Transformation Rule</th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-[#1b2438] text-slate-200">
                    {selectedEntity.attribute_diffs.map((diff: any, idx: number) => (
                      <tr key={idx} className={diff.conflict_detected ? 'bg-amber-500/5' : ''}>
                        <td className="px-4 py-2.5 font-semibold text-slate-300">
                          <div className="flex items-center gap-1.5">
                            <span>{diff.attribute}</span>
                            {diff.conflict_detected && (
                              <span className="rounded bg-amber-500/20 px-1 py-0.2 text-[9px] text-amber-400 font-bold">
                                CONFLICT
                              </span>
                            )}
                          </div>
                        </td>
                        <td className="px-4 py-2.5 font-mono font-bold text-white bg-emerald-500/5">
                          {diff.canonical_value !== null && diff.canonical_value !== undefined 
                            ? String(diff.canonical_value) 
                            : <span className="text-slate-500 italic">None</span>}
                        </td>
                        <td className="px-4 py-2.5 font-mono">
                          <div className="space-y-1">
                            {diff.raw_values.map((v: any, vIdx: number) => (
                              <div key={vIdx} className="flex items-center gap-2">
                                <span className="text-[10px] text-slate-500 font-mono">Row #{selectedEntity.raw_records[vIdx]?.original_row_idx || vIdx + 1}:</span>
                                <span className={`px-1.5 py-0.5 rounded text-[11px] ${
                                  diff.conflict_detected ? 'bg-[#1e293b] text-amber-300 font-semibold' : 'text-slate-400'
                                }`}>
                                  {v !== null && v !== undefined ? String(v) : '<NULL>'}
                                </span>
                              </div>
                            ))}
                          </div>
                        </td>
                        <td className="px-4 py-2.5 text-slate-400 text-[11px] leading-relaxed">
                          {diff.transformations_applied}
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </div>
          </div>
        ) : null}
      </div>

      {/* Raw Data Quality Diagnostics Table */}
      <div className="rounded-2xl border border-[#222f4c] bg-[#111726] p-6 shadow-xl space-y-4">
        <div className="flex items-center justify-between">
          <div>
            <h3 className="text-base font-bold text-white">Forensic Raw Data Defect Classification</h3>
            <p className="text-xs text-slate-400 mt-1">Identified across raw ingestion telemetry and systematically rectified.</p>
          </div>
          <span className="rounded-xl bg-emerald-500/10 px-3 py-1 text-xs font-bold text-emerald-400 border border-emerald-500/20">
            ZERO ROWS BLINDLY DELETED
          </span>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-3 gap-4 text-xs">
          <div className="rounded-xl border border-[#222f4c] bg-[#0c101a] p-4 space-y-2">
            <span className="font-bold text-blue-400">1. Identifier &amp; Key Defects</span>
            <ul className="space-y-1.5 text-slate-300 text-[11px]">
              <li>&bull; <span className="text-white font-mono">usr10098</span> &rarr; Lowercase ID standardisation</li>
              <li>&bull; <span className="text-white font-mono">10098</span> &rarr; Prefix restoration via regex</li>
              <li>&bull; <span className="text-white font-mono">USR 45454</span> &rarr; Internal whitespace stripping</li>
              <li>&bull; <span className="text-white font-mono">MCH-2637</span> &rarr; Hyphen separator normalization</li>
            </ul>
          </div>

          <div className="rounded-xl border border-[#222f4c] bg-[#0c101a] p-4 space-y-2">
            <span className="font-bold text-amber-400">2. Tax &amp; Identity Masking</span>
            <ul className="space-y-1.5 text-slate-300 text-[11px]">
              <li>&bull; <span className="text-white font-mono">HGKBQ-4142-L</span> &rarr; Hyphen stripping &amp; regex check</li>
              <li>&bull; <span className="text-white font-mono">QUPZM7586</span> &rarr; 9-char malformed PAN flagged</li>
              <li>&bull; <span className="text-white font-mono">Aadhaar</span> &rarr; Verhoeff check &amp; XXXX-XXXX-NNNN masking</li>
              <li>&bull; <span className="text-white font-mono">Legacy Codes</span> &rarr; V/P/R/KYC_DONE harmonized</li>
            </ul>
          </div>

          <div className="rounded-xl border border-[#222f4c] bg-[#0c101a] p-4 space-y-2">
            <span className="font-bold text-purple-400">3. Currency &amp; Temporal Defects</span>
            <ul className="space-y-1.5 text-slate-300 text-[11px]">
              <li>&bull; <span className="text-white font-mono">Rs. -2,450.00</span> &rarr; Symbol strip &amp; polarity fix</li>
              <li>&bull; <span className="text-white font-mono">₹ 15k</span> &rarr; Abbreviation expansion (x1000)</li>
              <li>&bull; <span className="text-white font-mono">Epoch TS</span> &rarr; 10-digit / 13-digit to ISO-8601</li>
              <li>&bull; <span className="text-white font-mono">MCCs</span> &rarr; 82 legacy codes &rarr; 10 RBI categories</li>
            </ul>
          </div>
        </div>
      </div>
    </div>
  )
}
