'use client';
import { useEffect, useState } from 'react';

const API_URL = process.env.NEXT_PUBLIC_API_URL || '';

export default function TaxonomyPanel() {
  const [taxonomy, setTaxonomy] = useState<{layers: string[], categories: string[]}>({layers: [], categories: []});
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetch(`${API_URL}/api/taxonomy`)
      .then(res => {
        if (!res.ok) throw new Error(`HTTP error! status: ${res.status}`);
        return res.json();
      })
      .then(data => {
        if (data && Array.isArray(data.layers) && Array.isArray(data.categories)) {
          setTaxonomy(data);
        } else {
          console.error("Invalid taxonomy data format:", data);
        }
        setLoading(false);
      })
      .catch(err => {
        console.error("Failed to fetch taxonomy:", err);
        setLoading(false);
      });
  }, []);

  if (loading) return <div className="text-gray-400 animate-pulse text-sm">Syncing taxonomy...</div>;

  const { layers = [], categories = [] } = taxonomy || {};

  return (
    <div>
      <h2 className="text-xl font-bold mb-4">Taxonomy</h2>
      <div className="space-y-6">
        <div>
          <h3 className="text-[10px] font-black text-gray-400 uppercase tracking-tighter mb-3">Layers</h3>
          <ul className="space-y-1">
            {layers.length > 0 ? layers.map(layer => (
              <li key={layer} className="text-xs font-medium text-gray-600 hover:text-blue-600 cursor-pointer transition-colors px-2 py-1.5 rounded-md hover:bg-blue-50/50 border border-transparent hover:border-blue-100">
                {layer}
              </li>
            )) : <li className="text-xs text-gray-400 italic font-light px-2">No layers mapped</li>}
          </ul>
        </div>
        <div>
          <h3 className="text-[10px] font-black text-gray-400 uppercase tracking-tighter mb-3">Core Categories</h3>
          <ul className="space-y-1">
            {categories.length > 0 ? categories.slice(0, 15).map(cat => (
              <li key={cat} className="text-xs font-medium text-gray-600 hover:text-blue-600 cursor-pointer transition-colors px-2 py-1.5 rounded-md hover:bg-blue-50/50 border border-transparent hover:border-blue-100">
                {cat}
              </li>
            )) : <li className="text-xs text-gray-400 italic font-light px-2">Loading categories...</li>}
            {categories.length > 15 && <li className="text-[10px] text-gray-300 pl-2 pt-1">+ {categories.length - 15} more</li>}
          </ul>
        </div>
      </div>
    </div>
  );
}
