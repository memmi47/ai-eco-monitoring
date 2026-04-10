'use client';

const DIRECTION_STYLES = {
  bullish: {
    badge: 'bg-emerald-500/20 text-emerald-400 border border-emerald-500/30',
    icon: '▲',
    dot: 'bg-emerald-400',
    glow: 'shadow-emerald-500/10',
    border: 'border-emerald-500/20',
  },
  bearish: {
    badge: 'bg-red-500/20 text-red-400 border border-red-500/30',
    icon: '▼',
    dot: 'bg-red-400',
    glow: 'shadow-red-500/10',
    border: 'border-red-500/20',
  },
};

const STRENGTH_STYLES: Record<string, string> = {
  strong: 'bg-white/15 text-white',
  moderate: 'bg-white/10 text-gray-300',
  weak: 'bg-white/5 text-gray-500',
};

const CONFIDENCE_LABEL: Record<string, string> = {
  high: 'High Conf.',
  medium: 'Med. Conf.',
  low: 'Low Conf.',
};

const MEMORY_CHIP_COLORS: Record<string, string> = {
  'HBM': 'bg-violet-500/25 text-violet-300 border border-violet-500/30',
  'Conv. DRAM': 'bg-blue-500/25 text-blue-300 border border-blue-500/30',
  'NAND': 'bg-amber-500/25 text-amber-300 border border-amber-500/30',
  'LPDDR': 'bg-cyan-500/25 text-cyan-300 border border-cyan-500/30',
};

const TIER_BADGES: Record<string, string> = {
  tier1: 'bg-orange-500/20 text-orange-300 border border-orange-500/30',
  tier2: 'bg-purple-500/20 text-purple-300 border border-purple-500/30',
  tier3: 'bg-sky-500/20 text-sky-300 border border-sky-500/30',
};

const TIME_LAG_LABELS: Record<string, string> = {
  'immediate': '즉시',
  'short_3-6m': '3-6개월',
  'mid_6-12m': '6-12개월',
  'long_12m+': '12개월+',
};

interface SignalCardProps {
  signal: {
    id?: number;
    company_name?: string;
    category?: string;
    layer?: string;
    stage2_variable_id?: string;
    stage2_variable_name?: string;
    stage2_direction?: string;
    stage2_caveat?: string;
    stage2_needs_review?: number;
    stage2_strength?: string;
    stage2_confidence?: string;
    stage2_affected_memory?: string[] | string;
    stage2_reasoning?: string;
    stage3_transmission_path?: string;
    stage3_time_lag?: string;
    stage3_demand_formula_tier?: string;
    stage3_decision_relevance?: string;
    stage3_counterargument?: string;
    stage3_executive_summary?: string;
    analyzed_at?: string;
  };
}

export default function SignalCard({ signal }: SignalCardProps) {
  const direction = signal.stage2_direction || 'bullish';
  const style = DIRECTION_STYLES[direction as keyof typeof DIRECTION_STYLES] || DIRECTION_STYLES.bullish;
  const tier = signal.stage3_demand_formula_tier || 'tier1';

  let memoryChips: string[] = [];
  if (Array.isArray(signal.stage2_affected_memory)) {
    memoryChips = signal.stage2_affected_memory;
  } else if (typeof signal.stage2_affected_memory === 'string') {
    try { memoryChips = JSON.parse(signal.stage2_affected_memory); } catch { memoryChips = []; }
  }

  const date = signal.analyzed_at ? new Date(signal.analyzed_at).toLocaleDateString('ko-KR') : '';

  return (
    <div className={`
      group relative bg-white/[0.04] border ${style.border} rounded-xl p-5
      hover:bg-white/[0.07] transition-all duration-300 shadow-lg ${style.glow}
      backdrop-blur-sm
    `}>
      {/* Header */}
      <div className="flex items-start justify-between gap-3 mb-3">
        <div className="flex flex-wrap items-center gap-2">
          {tier && (
            <span className={`text-[10px] font-bold px-2 py-0.5 rounded-full ${TIER_BADGES[tier] || 'bg-white/10 text-gray-400'}`}>
              {tier.toUpperCase()}
            </span>
          )}
          <span className="text-sm font-semibold text-white">{signal.company_name || '—'}</span>
          {signal.category && (
            <span className="text-[10px] text-gray-500 font-mono">{signal.category.split('.')[0]?.trim()}</span>
          )}
        </div>
        {signal.stage2_needs_review === 1 && (
          <span className="text-[10px] bg-yellow-500/20 text-yellow-400 border border-yellow-500/30 px-2 py-0.5 rounded-full whitespace-nowrap">
            ⚑ 검토 필요
          </span>
        )}
      </div>

      {/* Variable + Signal Direction */}
      <div className="flex flex-wrap items-center gap-2 mb-3">
        {signal.stage2_variable_id && (
          <span className="text-[11px] font-mono text-gray-500">{signal.stage2_variable_id}</span>
        )}
        <span className="text-xs text-gray-400 truncate max-w-[180px]">{signal.stage2_variable_name}</span>
      </div>

      <div className="flex flex-wrap items-center gap-2 mb-4">
        <span className={`inline-flex items-center gap-1 text-xs font-bold px-3 py-1 rounded-full ${style.badge}`}>
          <span>{style.icon}</span>
          <span>{direction === 'bullish' ? 'Bullish' : 'Bearish'}</span>
        </span>
        {signal.stage2_strength && (
          <span className={`text-[11px] px-2 py-0.5 rounded-full ${STRENGTH_STYLES[signal.stage2_strength] || STRENGTH_STYLES.moderate}`}>
            {signal.stage2_strength.charAt(0).toUpperCase() + signal.stage2_strength.slice(1)}
          </span>
        )}
        {signal.stage2_confidence && (
          <span className="text-[10px] text-gray-500">{CONFIDENCE_LABEL[signal.stage2_confidence]}</span>
        )}
      </div>

      {/* Memory Chips */}
      {memoryChips.length > 0 && (
        <div className="flex flex-wrap gap-1.5 mb-4">
          {memoryChips.map((mem) => (
            <span key={mem} className={`text-[10px] font-bold px-2 py-0.5 rounded-md ${MEMORY_CHIP_COLORS[mem] || 'bg-white/10 text-gray-400'}`}>
              {mem}
            </span>
          ))}
        </div>
      )}

      {/* Transmission Path */}
      {signal.stage3_transmission_path && (
        <div className="bg-white/5 rounded-lg p-3 mb-3 border border-white/5">
          <p className="text-[10px] font-semibold text-gray-500 uppercase tracking-wider mb-1">전이 경로</p>
          <p className="text-xs text-gray-300 leading-relaxed">{signal.stage3_transmission_path}</p>
        </div>
      )}

      {/* Executive Summary */}
      {signal.stage3_executive_summary && (
        <div className="mb-3">
          <p className="text-[10px] font-semibold text-gray-500 uppercase tracking-wider mb-1">경영진 요약</p>
          <p className="text-xs text-gray-300 leading-relaxed">{signal.stage3_executive_summary}</p>
        </div>
      )}

      {/* Caveat */}
      {signal.stage2_caveat && (
        <div className="bg-yellow-500/5 border border-yellow-500/15 rounded-lg p-2.5 mb-3">
          <p className="text-[10px] text-yellow-400/80 leading-relaxed">⚠ {signal.stage2_caveat}</p>
        </div>
      )}

      {/* Counterargument (Stage 3) */}
      {signal.stage3_counterargument && (
        <div className="bg-slate-500/5 border border-slate-500/15 rounded-lg p-2.5 mb-3">
          <p className="text-[10px] font-semibold text-slate-500 uppercase tracking-wider mb-1">반론</p>
          <p className="text-[10px] text-slate-400/80 leading-relaxed">↩ {signal.stage3_counterargument}</p>
        </div>
      )}

      {/* Footer */}
      <div className="flex items-center justify-between mt-3 pt-3 border-t border-white/5">
        <div className="flex items-center gap-3">
          {signal.stage3_time_lag && (
            <span className="text-[10px] text-gray-500">
              ⏱ {TIME_LAG_LABELS[signal.stage3_time_lag] || signal.stage3_time_lag}
            </span>
          )}
          {signal.stage3_decision_relevance && (
            <span className="text-[10px] text-gray-600">{signal.stage3_decision_relevance.replace(/_/g,' ')}</span>
          )}
        </div>
        {date && <span className="text-[10px] text-gray-600">{date}</span>}
      </div>
    </div>
  );
}
