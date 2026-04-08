import NewsFeed from "@/components/NewsFeed";
import ActivityChart from "@/components/ActivityChart";
import TaxonomyPanel from "@/components/TaxonomyPanel";

export default function Home() {
  return (
    <main className="min-h-screen p-8 max-w-7xl mx-auto space-y-8">
      <header className="mb-8">
        <h1 className="text-3xl font-bold">AI Eco Monitor Dashboard</h1>
        <p className="text-gray-600">Memory semiconductor impact analysis</p>
      </header>
      
      <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
        <div className="md:col-span-1 border rounded-lg bg-white p-4 shadow-sm">
          <TaxonomyPanel />
        </div>
        <div className="md:col-span-2 space-y-6">
          <div className="border rounded-lg bg-white p-4 shadow-sm min-h-[300px]">
            <ActivityChart />
          </div>
          <div className="border rounded-lg bg-white p-4 shadow-sm min-h-[300px]">
            <NewsFeed />
          </div>
        </div>
      </div>
    </main>
  );
}
