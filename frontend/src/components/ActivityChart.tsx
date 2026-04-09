'use client';

import { useEffect, useState } from 'react';

const API_URL = process.env.NEXT_PUBLIC_API_URL || '';

interface DriverScore {
  driver_id: string;
  driver_name: string;
  score: number;
  count: number;
  bullish: number;
  bearish: number;
  direction: string;
}

interface Stats {
  total_companies: number;
  tier1: number;
  tier2: number;
  tier3: number;
}

const DRIVER_COLORS: Record<string, { bar: string; text: string; bg: string }> = {
  MD1: { bar: 'from-orange-500 to-orange-400', text: 'text-orange-400', bg: 'bg-orange-500/10' },
  MD2: { bar: 'from-violet-500 to-violet-400', text: 'text-violet-400', bg: 'bg-violet-500/10' },
  MD3: { bar: 'from-blue-500 to-blue-400',     text: 'text-blue-400',   bg: 'bg-blue-500/10' },
  MD4: { bar: 'from-emerald-500 to-emerald-400', text: 'text-emerald-400', bg: 'bg-emerald-500/10' },
  MD5: { bar: 'from-pink-500 to-pink-400',     text: 'text-pink-400',   bg: 'bg-pink-500/10' },
};

export default function ActivityChart() {
  const [drivers, setDrivers] = useState<DriverScore[]>([]);
  const [stats, setStats] = useState<Stats>({ total_companies: 0, tier1: 0, tier2: 0, tier3: 0 });
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    Promise.all([
      fetch(`${API_URL}/api/drivers`).then(r => r.ok ? r.json() : []).catch(() => []),
      fetch(`${API_URL}/api/stats`).then(r => r.ok ? r.json() : {}).catch(() => ({})),
    ]).then(([d, s]) => {
      if (Array.isArray(d)) setDrivers(d);
      const stats = s as any;
      if (stats && typeof stats.total_companies === 'number') setStats(stats as Stats);
      setLoading(false);
    });
  }, []);

  if (loading) {
    return (
      <div className="animate-pulse space-y-3">
        {[...Array(5)].map((_, i) => <div key={i} className="h-10 bg-white/5 rounded-lg" />)}
      </div>
    );
  }

  const hasDriverData = drivers.some(d => d.count > 0);

  return (
    <div className="space-y-6">
      {/* Ecosystem Stats */}
      <div>
        <h2 className="text-[10px] font-black text-gray-400 uppercase tracking-widest mb-3">
          Ecosystem Overview
        </h2>
        <div className="grid grid-cols-2 gap-2">
          {[
            { label: 'Total Players', val: stats.total_companies, color: 'text-white' },
            { label: 'Tier 1 (High)', val: stats.tier1, color: 'text-red-400' },
            { label: 'Tier 2 (Med)', val: stats.tier2, color: 'text-orange-400' },
            { label: 'Tier 3 (Low)', val: stats.tier3, color: 'text-yellow-500' },
          ].map((item, idx) => (
            <div key={idx} className="bg-white/[0.04] rounded-lg p-3 border border-white/5 text-center">
              <div className={`text-xl font-black ${item.color}`}>{item.val}</div>
              <div className="text-[10px] text-gray-500 mt-0.5">{item.label}</div>
            </div>
          ))}
        </div>
      </div>

      {/* Memory Demand Drivers */}
      <div>
        <h2 className="text-[10px] font-black text-gray-400 uppercase tracking-widest mb-3">
          Memory Demand Drivers
          {!hasDriverData && (
            <span className="ml-2 text-gray-600 normal-case font-normal">
              (분석 데이터 없음)
            </span>
          )}
        </h2>
        <div className="space-y-2.5">
          {drivers.map((d) => {
            const color = DRIVER_COLORS[d.driver_id] || DRIVER_COLORS.MD1;
            const isBullish = d.direction === 'bullish';
            const isNeutral = d.direction === 'neutral' || d.count === 0;
            // 바 너비: 점수 절댓값 기반 (최대 ±15 → 100%)
            const barWidth = Math.min(Math.abs(d.score) / 15 * 100, 100);

            return (
              <div key={d.driver_id} className={`rounded-lg p-3 border border-white/5 ${color.bg}`}>
                <div className="flex items-center justify-between mb-2">
                  <div className="flex items-center gap-2">
                    <span className={`text-[10px] font-black ${color.text} font-mono`}>{d.driver_id}</span>
                    <span className="text-[11px] text-gray-400 leading-tight">{d.driver_name}</span>
                  </div>
                  <div className="flex items-center gap-2">
                    {d.count > 0 && (
                      <span className="text-[10px] text-gray-600">{d.count}건</span>
                    )}
                    {isNeutral ? (
                      <span className="text-[10px] text-gray-600 px-2 py-0.5 bg-white/5 rounded-full">—</span>
                    ) : isBullish ? (
                      <span className="text-[10px] text-emerald-400 px-2 py-0.5 bg-emerald-500/10 rounded-full border border-emerald-500/20">
                        ▲ Bullish
                      </span>
                    ) : (
                      <span className="text-[10px] text-red-400 px-2 py-0.5 bg-red-500/10 rounded-full border border-red-500/20">
                        ▼ Bearish
                      </span>
                    )}
                  </div>
                </div>
                {/* Progress bar */}
                <div className="h-1.5 bg-white/5 rounded-full overflow-hidden">
                  {!isNeutral && (
                    <div
                      className={`h-full rounded-full bg-gradient-to-r ${isBullish ? color.bar : 'from-red-600 to-red-500'} transition-all duration-700`}
                      style={{ width: `${barWidth}%` }}
                    />
                  )}
                </div>
                {/* Bullish/Bearish counts */}
                {d.count > 0 && (
                  <div className="flex items-center gap-2 mt-1.5">
                    <span className="text-[9px] text-emerald-500">▲ {d.bullish}</span>
                    <span className="text-[9px] text-gray-600">/</span>
                    <span className="text-[9px] text-red-500">▼ {d.bearish}</span>
                  </div>
                )}
              </div>
            );
          })}
        </div>
      </div>
    </div>
  );
}
