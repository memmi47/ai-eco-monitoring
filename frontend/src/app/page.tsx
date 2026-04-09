'use client';

import { useState } from 'react';
import NewsFeed from '@/components/NewsFeed';
import ActivityChart from '@/components/ActivityChart';
import TaxonomyPanel from '@/components/TaxonomyPanel';
import DivergenceAlert from '@/components/DivergenceAlert';
import EventCalendar from '@/components/EventCalendar';

type Tab = 'signals' | 'events';

export default function Home() {
  const [activeTab, setActiveTab] = useState<Tab>('signals');

  return (
    <main className="min-h-screen bg-[#070B14] text-white">
      {/* ── HEADER ── */}
      <header className="border-b border-white/5 bg-black/20 backdrop-blur-sm sticky top-0 z-50">
        <div className="max-w-[1400px] mx-auto px-6 py-4 flex items-center justify-between">
          <div className="flex items-center gap-3">
            <div className="h-8 w-8 rounded-lg bg-gradient-to-br from-violet-500 to-blue-500 flex items-center justify-center text-white text-sm font-black">
              AI
            </div>
            <div>
              <h1 className="text-sm font-bold text-white tracking-tight">AI Eco Monitor</h1>
              <p className="text-[10px] text-gray-500">Memory Semiconductor Demand Intelligence</p>
            </div>
          </div>
          <div className="flex items-center gap-2">
            <span className="text-[10px] bg-emerald-500/10 text-emerald-400 border border-emerald-500/20 px-3 py-1 rounded-full font-medium">
              ● Live
            </span>
            <span className="text-[10px] bg-violet-500/10 text-violet-400 border border-violet-500/20 px-2 py-1 rounded-full font-mono">
              Pipeline v2
            </span>
          </div>
        </div>
      </header>

      <div className="max-w-[1400px] mx-auto px-6 py-6">
        {/* ── DIVERGENCE ALERTS ── */}
        <DivergenceAlert />

        {/* ── MAIN LAYOUT ── */}
        <div className="grid grid-cols-[280px_1fr_320px] gap-6">

          {/* ── LEFT: TAXONOMY PANEL ── */}
          <div className="bg-white/[0.03] border border-white/[0.06] rounded-2xl p-5 h-fit sticky top-[73px]">
            <TaxonomyPanel />
          </div>

          {/* ── CENTER: TABBED CONTENT ── */}
          <div className="min-w-0">
            {/* Tab Navigation */}
            <div className="flex items-center gap-1 mb-5 bg-white/[0.04] p-1 rounded-xl border border-white/[0.06] w-fit">
              <button
                onClick={() => setActiveTab('signals')}
                className={`px-4 py-2 rounded-lg text-xs font-bold transition-all ${
                  activeTab === 'signals'
                    ? 'bg-white/10 text-white shadow-sm'
                    : 'text-gray-500 hover:text-gray-300'
                }`}
              >
                📡 Signal Feed
              </button>
              <button
                onClick={() => setActiveTab('events')}
                className={`px-4 py-2 rounded-lg text-xs font-bold transition-all ${
                  activeTab === 'events'
                    ? 'bg-white/10 text-white shadow-sm'
                    : 'text-gray-500 hover:text-gray-300'
                }`}
              >
                📅 Event Calendar
              </button>
            </div>

            {/* Tab Content */}
            <div className="bg-white/[0.03] border border-white/[0.06] rounded-2xl p-5">
              {activeTab === 'signals' && <NewsFeed />}
              {activeTab === 'events' && <EventCalendar />}
            </div>
          </div>

          {/* ── RIGHT: ACTIVITY CHART (Driver Scores) ── */}
          <div className="bg-white/[0.03] border border-white/[0.06] rounded-2xl p-5 h-fit sticky top-[73px]">
            <ActivityChart />
          </div>
        </div>
      </div>
    </main>
  );
}
