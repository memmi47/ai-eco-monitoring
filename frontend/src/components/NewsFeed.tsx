'use client';
import { useEffect, useState } from 'react';

const API_URL = process.env.NEXT_PUBLIC_API_URL || '';

interface Company {
  id: number;
  company_name: string;
  layer: string;
  biz_type: string;
  tier: string;
  importance: string;
}

export default function NewsFeed() {
  const [companies, setCompanies] = useState<Company[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetch(`${API_URL}/api/companies?tier=T1`) // Fetch Tier 1 companies as "Important Updates"
      .then(res => res.json())
      .then(data => {
        setCompanies(data.slice(0, 10)); // Show top 10 for feed
        setLoading(false);
      })
      .catch(err => {
        console.error("Failed to fetch companies for feed:", err);
        setLoading(false);
      });
  }, []);

  if (loading) return <div className="text-gray-400">Syncing with ecosystem data...</div>;

  return (
    <div>
      <h2 className="text-xl font-bold mb-4">Ecosystem Tier-1 Watchlist</h2>
      <div className="space-y-4">
        {companies.length === 0 ? (
          <div className="text-gray-500 italic">No high-priority companies detected in database.</div>
        ) : (
          companies.map(company => (
            <div key={company.id} className="p-3 border-l-4 border-blue-500 bg-blue-50/30 rounded-r shadow-sm">
              <div className="flex justify-between items-start">
                <h4 className="font-bold text-gray-800">{company.company_name}</h4>
                <span className="text-[10px] bg-blue-100 text-blue-700 px-2 py-0.5 rounded-full uppercase font-bold">
                  {company.tier}
                </span>
              </div>
              <p className="text-xs text-gray-600 mt-1">{company.layer} • {company.biz_type}</p>
              <div className="mt-2 text-[11px] text-blue-600 font-medium">
                Analysis: High influence ecosystem player
              </div>
            </div>
          ))
        )}
      </div>
    </div>
  );
}
