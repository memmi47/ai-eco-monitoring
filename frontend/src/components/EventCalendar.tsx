'use client';

import { useEffect, useState } from 'react';

const API_URL = process.env.NEXT_PUBLIC_API_URL || '';

interface ExpectedEvent {
  id: number;
  company_name?: string;
  event_type: string;
  expected_date: string;
  description?: string;
  variable_ids?: string[];
  source?: string;
  is_confirmed?: number;
}

const EVENT_TYPE_STYLES: Record<string, { bg: string; text: string; icon: string }> = {
  earnings:       { bg: 'bg-blue-500/20 border-blue-500/30',  text: 'text-blue-300',  icon: '📊' },
  product_launch: { bg: 'bg-violet-500/20 border-violet-500/30', text: 'text-violet-300', icon: '🚀' },
  conference:     { bg: 'bg-amber-500/20 border-amber-500/30', text: 'text-amber-300', icon: '🎤' },
  regulatory:     { bg: 'bg-red-500/20 border-red-500/30',   text: 'text-red-300',   icon: '⚖' },
  industry_data:  { bg: 'bg-emerald-500/20 border-emerald-500/30', text: 'text-emerald-300', icon: '📈' },
};

const EVENT_TYPE_LABELS: Record<string, string> = {
  earnings: '실적 발표',
  product_launch: '제품 출시',
  conference: '컨퍼런스',
  regulatory: '규제/정책',
  industry_data: '산업 통계',
};

// 날짜를 주차별로 그룹화
function groupByWeek(events: ExpectedEvent[]): Record<string, ExpectedEvent[]> {
  const groups: Record<string, ExpectedEvent[]> = {};
  events.forEach(evt => {
    const date = new Date(evt.expected_date);
    // 해당 주의 월요일 날짜 계산
    const day = date.getDay();
    const diff = date.getDate() - day + (day === 0 ? -6 : 1);
    const monday = new Date(date);
    monday.setDate(diff);
    const key = monday.toISOString().split('T')[0];
    if (!groups[key]) groups[key] = [];
    groups[key].push(evt);
  });
  return groups;
}

function getWeekLabel(mondayStr: string): string {
  const monday = new Date(mondayStr);
  const friday = new Date(monday);
  friday.setDate(monday.getDate() + 4);
  const now = new Date();
  const thisMonday = new Date(now);
  const dayOfWeek = now.getDay();
  const diffToMonday = dayOfWeek === 0 ? -6 : 1 - dayOfWeek;
  thisMonday.setDate(now.getDate() + diffToMonday);
  thisMonday.setHours(0,0,0,0);
  monday.setHours(0,0,0,0);

  const weekDiff = Math.round((monday.getTime() - thisMonday.getTime()) / (7 * 24 * 60 * 60 * 1000));
  let label = '';
  if (weekDiff === 0) label = '이번 주';
  else if (weekDiff === 1) label = '다음 주';
  else label = `${weekDiff}주 후`;

  const m1 = monday.getMonth() + 1;
  const d1 = monday.getDate();
  const m2 = friday.getMonth() + 1;
  const d2 = friday.getDate();
  return `${label} (${m1}/${d1}-${m2}/${d2})`;
}

export default function EventCalendar() {
  const [events, setEvents] = useState<ExpectedEvent[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetch(`${API_URL}/api/expected-events?weeks=5`)
      .then(res => res.ok ? res.json() : [])
      .then(data => {
        if (Array.isArray(data)) setEvents(data);
        setLoading(false);
      })
      .catch(() => setLoading(false));
  }, []);

  if (loading) {
    return (
      <div className="flex items-center justify-center h-40">
        <div className="text-gray-500 text-sm animate-pulse">이벤트 캘린더 로딩 중...</div>
      </div>
    );
  }

  if (events.length === 0) {
    return (
      <div className="flex flex-col items-center justify-center h-48 gap-3">
        <div className="text-4xl opacity-30">📅</div>
        <p className="text-gray-500 text-sm text-center">
          등록된 예정 이벤트가 없습니다.
        </p>
        <p className="text-gray-600 text-xs text-center">
          실적 발표, 제품 출시, 컨퍼런스 등을<br/>
          <code className="text-gray-500">POST /api/expected-events</code>로 등록하세요.
        </p>
      </div>
    );
  }

  const grouped = groupByWeek(events);
  const weeks = Object.keys(grouped).sort();

  return (
    <div className="space-y-6">
      {weeks.map(weekKey => (
        <div key={weekKey}>
          <h3 className="text-xs font-bold text-gray-400 uppercase tracking-widest mb-3 flex items-center gap-2">
            <span className="h-px flex-1 bg-white/5"/>
            {getWeekLabel(weekKey)}
            <span className="h-px flex-1 bg-white/5"/>
          </h3>
          <div className="space-y-2">
            {grouped[weekKey].map(evt => {
              const typeStyle = EVENT_TYPE_STYLES[evt.event_type] || EVENT_TYPE_STYLES.earnings;
              const dateStr = new Date(evt.expected_date).toLocaleDateString('ko-KR', { month: 'numeric', day: 'numeric', weekday: 'short' });

              return (
                <div key={evt.id} className={`
                  flex items-start gap-3 p-3 rounded-lg border
                  ${typeStyle.bg} backdrop-blur-sm
                  hover:bg-white/5 transition-colors
                `}>
                  <div className="flex-shrink-0 w-12 text-center">
                    <div className="text-lg">{typeStyle.icon}</div>
                    <div className="text-[10px] text-gray-500 leading-tight">{dateStr}</div>
                  </div>
                  <div className="flex-1 min-w-0">
                    <div className="flex items-center gap-2 mb-1 flex-wrap">
                      {evt.company_name && (
                        <span className="text-xs font-semibold text-white">{evt.company_name}</span>
                      )}
                      <span className={`text-[10px] px-2 py-0.5 rounded-full border ${typeStyle.bg} ${typeStyle.text}`}>
                        {EVENT_TYPE_LABELS[evt.event_type] || evt.event_type}
                      </span>
                      {evt.is_confirmed === 0 && (
                        <span className="text-[10px] text-gray-500">미확정</span>
                      )}
                    </div>
                    {evt.description && (
                      <p className="text-xs text-gray-400 leading-relaxed">{evt.description}</p>
                    )}
                    {evt.variable_ids && evt.variable_ids.length > 0 && (
                      <div className="flex gap-1 mt-1.5 flex-wrap">
                        {evt.variable_ids.map(vid => (
                          <span key={vid} className="text-[10px] font-mono bg-white/5 text-gray-500 px-1.5 py-0.5 rounded">
                            {vid}
                          </span>
                        ))}
                      </div>
                    )}
                  </div>
                </div>
              );
            })}
          </div>
        </div>
      ))}
    </div>
  );
}
