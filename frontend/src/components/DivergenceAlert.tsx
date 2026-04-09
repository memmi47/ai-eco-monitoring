'use client';

import { useEffect, useState } from 'react';

const API_URL = process.env.NEXT_PUBLIC_API_URL || '';

interface Alert {
  id: string;
  name: string;
  condition: string;
  message: string;
  active: boolean;
}

const ALERT_STYLES: Record<string, { bg: string; border: string; icon: string; accent: string }> = {
  DA1: { bg: 'from-orange-950/80 to-orange-900/40', border: 'border-orange-500/30', icon: '⚡', accent: 'text-orange-400' },
  DA2: { bg: 'from-red-950/80 to-red-900/40', border: 'border-red-500/30', icon: '🔴', accent: 'text-red-400' },
  DA3: { bg: 'from-purple-950/80 to-purple-900/40', border: 'border-purple-500/30', icon: '📉', accent: 'text-purple-400' },
  DA4: { bg: 'from-red-950/90 to-slate-900/80', border: 'border-red-600/50', icon: '🚨', accent: 'text-red-300' },
  DA5: { bg: 'from-emerald-950/80 to-emerald-900/40', border: 'border-emerald-500/30', icon: '🚀', accent: 'text-emerald-400' },
};

export default function DivergenceAlert() {
  const [alerts, setAlerts] = useState<Alert[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetch(`${API_URL}/api/divergence-alerts`)
      .then(res => res.ok ? res.json() : null)
      .then(data => {
        if (data?.active_alerts) setAlerts(data.active_alerts);
        setLoading(false);
      })
      .catch(() => setLoading(false));
  }, []);

  if (loading || alerts.length === 0) return null;

  return (
    <div className="space-y-2 mb-6">
      {alerts.map(alert => {
        const style = ALERT_STYLES[alert.id] || ALERT_STYLES.DA1;
        return (
          <div key={alert.id} className={`
            relative flex items-start gap-4 p-4 rounded-xl
            bg-gradient-to-r ${style.bg}
            border ${style.border}
            backdrop-blur-sm
          `}>
            {/* Pulse dot */}
            <div className="flex-shrink-0 mt-0.5">
              <span className="relative flex h-3 w-3">
                <span className={`animate-ping absolute inline-flex h-full w-full rounded-full opacity-75 ${alert.id === 'DA5' ? 'bg-emerald-400' : 'bg-red-400'}`}/>
                <span className={`relative inline-flex rounded-full h-3 w-3 ${alert.id === 'DA5' ? 'bg-emerald-500' : 'bg-red-500'}`}/>
              </span>
            </div>

            <div className="flex-1 min-w-0">
              <div className="flex items-center gap-2 mb-1">
                <span className="text-sm">{style.icon}</span>
                <span className={`text-sm font-bold ${style.accent}`}>{alert.name}</span>
                <span className="text-[10px] bg-white/10 text-gray-400 px-2 py-0.5 rounded-full font-mono">{alert.id}</span>
              </div>
              <p className="text-xs text-gray-300 leading-relaxed">{alert.message}</p>
            </div>
          </div>
        );
      })}
    </div>
  );
}
