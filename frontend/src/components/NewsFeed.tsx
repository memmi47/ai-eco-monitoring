'use client';

import { useEffect, useState } from 'react';
import SignalCard from './SignalCard';

const API_URL = process.env.NEXT_PUBLIC_API_URL || '';

type FilterDirection = 'all' | 'bullish' | 'bearish';
type FilterTier = 'all' | 'tier1' | 'tier2' | 'tier3';
type FilterRelevance = 'default' | 'strategic';

const RELEVANCE_LABELS: Record<string, string> = {
  current_quarter:    '당분기',
  next_quarter:       '차분기',
  investment_plan:    '투자계획',
  strategic_reference:'전략참조',
};

export default function NewsFeed() {
  const [signals, setSignals] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);
  const [filterDir, setFilterDir] = useState<FilterDirection>('all');
  const [filterTier, setFilterTier] = useState<FilterTier>('all');
  const [filterRelevance, setFilterRelevance] = useState<FilterRelevance>('default');

  useEffect(() => {
    const params = new URLSearchParams({ limit: '30' });
    if (filterDir !== 'all') params.set('direction', filterDir);
    if (filterTier !== 'all') params.set('tier', filterTier);
    // design_v2: 기본 뷰는 strategic_reference 제외, strategic 뷰는 strategic_reference만 표시
    if (filterRelevance === 'default') {
      params.set('exclude_strategic', 'true');
    } else {
      params.set('decision_relevance', 'strategic_reference');
    }

    fetch(`${API_URL}/api/signals?${params}`)
      .then(res => res.ok ? res.json() : [])
      .then(data => {
        if (Array.isArray(data)) setSignals(data);
        setLoading(false);
      })
      .catch(() => setLoading(false));
  }, [filterDir, filterTier, filterRelevance]);

  const filterBtnBase = 'text-[10px] font-bold px-3 py-1 rounded-full transition-all border';
  const activeDir = (val: FilterDirection) =>
    filterDir === val
      ? (val === 'bullish' ? 'bg-emerald-500/20 text-emerald-400 border-emerald-500/30' :
         val === 'bearish' ? 'bg-red-500/20 text-red-400 border-red-500/30' :
         'bg-white/15 text-white border-white/20')
      : 'bg-white/5 text-gray-500 border-white/10 hover:bg-white/10';
  const activeTier = (val: FilterTier) =>
    filterTier === val
      ? 'bg-white/15 text-white border-white/20'
      : 'bg-white/5 text-gray-500 border-white/10 hover:bg-white/10';

  return (
    <div>
      <div className="flex items-center justify-between mb-4">
        <h2 className="text-[10px] font-black text-gray-400 uppercase tracking-widest">
          Signal Feed
        </h2>
        <span className="text-[10px] text-gray-600">{signals.length}건</span>
      </div>

      {/* Filters */}
      <div className="space-y-2 mb-5">
        <div className="flex gap-1.5 flex-wrap">
          <button className={`${filterBtnBase} ${activeDir('all')}`} onClick={() => setFilterDir('all')}>All</button>
          <button className={`${filterBtnBase} ${activeDir('bullish')}`} onClick={() => setFilterDir('bullish')}>▲ Bullish</button>
          <button className={`${filterBtnBase} ${activeDir('bearish')}`} onClick={() => setFilterDir('bearish')}>▼ Bearish</button>
        </div>
        <div className="flex gap-1.5 flex-wrap">
          <button className={`${filterBtnBase} ${activeTier('all')}`} onClick={() => setFilterTier('all')}>All Tiers</button>
          <button className={`${filterBtnBase} ${activeTier('tier1')}`} onClick={() => setFilterTier('tier1')}>T1 Infra</button>
          <button className={`${filterBtnBase} ${activeTier('tier2')}`} onClick={() => setFilterTier('tier2')}>T2 Model</button>
          <button className={`${filterBtnBase} ${activeTier('tier3')}`} onClick={() => setFilterTier('tier3')}>T3 App</button>
        </div>
        {/* Decision Relevance 뷰 전환 — design_v2: Strategic은 별도 뷰 */}
        <div className="flex gap-1.5 flex-wrap items-center">
          <span className="text-[10px] text-gray-600 font-semibold uppercase tracking-wider">뷰:</span>
          <button
            className={`${filterBtnBase} ${filterRelevance === 'default' ? 'bg-white/15 text-white border-white/20' : 'bg-white/5 text-gray-500 border-white/10 hover:bg-white/10'}`}
            onClick={() => setFilterRelevance('default')}
          >
            {RELEVANCE_LABELS['current_quarter']} · {RELEVANCE_LABELS['next_quarter']} · {RELEVANCE_LABELS['investment_plan']}
          </button>
          <button
            className={`${filterBtnBase} ${filterRelevance === 'strategic' ? 'bg-violet-500/20 text-violet-400 border-violet-500/30' : 'bg-white/5 text-gray-500 border-white/10 hover:bg-white/10'}`}
            onClick={() => setFilterRelevance('strategic')}
          >
            🔭 {RELEVANCE_LABELS['strategic_reference']}
          </button>
        </div>
      </div>

      {/* Signal Cards */}
      {loading ? (
        <div className="space-y-3">
          {[...Array(3)].map((_, i) => (
            <div key={i} className="h-40 bg-white/[0.03] rounded-xl animate-pulse border border-white/5" />
          ))}
        </div>
      ) : signals.length === 0 ? (
        <div className="flex flex-col items-center justify-center py-16 gap-4">
          <div className="text-4xl opacity-20">📡</div>
          <p className="text-sm text-gray-500 text-center">분석된 시그널이 없습니다.</p>
          <p className="text-xs text-gray-600 text-center leading-relaxed">
            <code className="text-gray-500">POST /api/analyze/v2</code>로<br/>
            뉴스를 분석하면 이 피드에 표시됩니다.
          </p>
        </div>
      ) : (
        <div className="space-y-3">
          {signals.map(signal => (
            <SignalCard key={signal.id} signal={signal} />
          ))}
        </div>
      )}
    </div>
  );
}
