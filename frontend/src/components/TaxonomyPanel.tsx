'use client';
import { useEffect, useState } from 'react';

const API_URL = process.env.NEXT_PUBLIC_API_URL || '';

export default function TaxonomyPanel() {
  const [taxonomy, setTaxonomy] = useState<{layers: string[], categories: string[]}>({layers: [], categories: []});
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetch(`${API_URL}/api/taxonomy`)
      .then(res => res.json())
      .then(data => {
        setTaxonomy(data);
        setLoading(false);
      })
      .catch(err => {
        console.error("Failed to fetch taxonomy:", err);
        setLoading(false);
      });
  }, []);

  if (loading) return <div className="text-gray-400">Loading taxonomy...</div>;

  return (
    <div>
      <h2 className="text-xl font-bold mb-4">Taxonomy</h2>
      <div className="space-y-6">
        <div>
          <h3 className="text-sm font-semibold text-gray-500 uppercase tracking-wider mb-2">Layers</h3>
          <ul className="space-y-1">
            {taxonomy.layers.map(layer => (
              <li key={layer} className="text-sm text-gray-700 hover:text-blue-600 cursor-pointer transition-colors px-2 py-1 rounded hover:bg-blue-50">
                {layer}
              </li>
            ))}
          </ul>
        </div>
        <div>
          <h3 className="text-sm font-semibold text-gray-500 uppercase tracking-wider mb-2">Key Categories</h3>
          <ul className="space-y-1">
            {taxonomy.categories.slice(0, 15).map(cat => (
              <li key={cat} className="text-sm text-gray-700 hover:text-blue-600 cursor-pointer transition-colors px-2 py-1 rounded hover:bg-blue-50">
                {cat}
              </li>
            ))}
            {taxonomy.categories.length > 15 && <li className="text-xs text-gray-400 pl-2">...and more</li>}
          </ul>
        </div>
      </div>
    </div>
  );
}
