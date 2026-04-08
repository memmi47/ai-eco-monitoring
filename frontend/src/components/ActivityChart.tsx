'use client';
import { useEffect, useState } from 'react';

const API_URL = process.env.NEXT_PUBLIC_API_URL || '';

export default function ActivityChart() {
  const [stats, setStats] = useState({total_companies: 0, tier1: 0, tier2: 0, tier3: 0});
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetch(`${API_URL}/api/stats`)
      .then(res => {
        if (!res.ok) throw new Error(`HTTP error! status: ${res.status}`);
        return res.json();
      })
      .then(data => {
        if (data && typeof data.total_companies === 'number') {
          setStats(data);
        }
        setLoading(false);
      })
      .catch(err => {
        console.error("Failed to fetch stats for chart:", err);
        setLoading(false);
      });
  }, []);

  if (loading) return <div className="text-gray-400 animate-pulse text-sm">Quantifying ecosystem impact...</div>;

  const displayStats = {
    total_companies: stats.total_companies || 0,
    tier1: stats.tier1 || 0,
    tier2: stats.tier2 || 0,
    tier3: stats.tier3 || 0
  };

  return (
    <div>
      <h2 className="text-xl font-bold mb-6">Ecosystem Summary</h2>
      <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
        {[
          { label: 'Total Players', val: displayStats.total_companies, color: 'text-gray-900' },
          { label: 'Tier 1 (High)', val: displayStats.tier1, color: 'text-red-600' },
          { label: 'Tier 2 (Med)', val: displayStats.tier2, color: 'text-orange-600' },
          { label: 'Tier 3 (Low)', val: displayStats.tier3, color: 'text-yellow-600' }
        ].map((item, idx) => (
          <div key={idx} className="bg-gray-50 p-4 rounded-lg text-center border border-gray-100 shadow-sm">
            <div className={`text-2xl font-black ${item.color}`}>{item.val}</div>
            <div className="text-[10px] text-gray-500 font-bold uppercase mt-1">{item.label}</div>
          </div>
        ))}
      </div>
      <div className="mt-8 p-4 bg-gradient-to-r from-blue-600 to-indigo-700 rounded-xl text-white shadow-lg">
        <div className="text-xs opacity-80 font-medium">Memory Semiconductor Impact Index</div>
        <div className="text-3xl font-black mt-1">78.5</div>
        <div className="text-[10px] bg-white/20 inline-block px-2 py-0.5 rounded-full mt-2">↑ 2.4% from last week</div>
      </div>
    </div>
  );
}
