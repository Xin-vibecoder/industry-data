import type { Metadata } from 'next';
import Link from 'next/link';

export const metadata: Metadata = {
  title: '同花顺行业数据',
  description: '查看90个行业的历史数据',
};

interface Sector {
  id: number;
  name: string;
  code: string;
  created_at: string;
}

async function getSectors(): Promise<Sector[]> {
  const res = await fetch(`${process.env.NEXT_PUBLIC_API_URL || 'http://localhost:5000'}/api/sectors`, {
    cache: 'no-store',
  });
  
  if (!res.ok) {
    return [];
  }
  
  return res.json();
}

export default async function Home() {
  const sectors = await getSectors();

  return (
    <div className="min-h-screen bg-background p-8">
      <div className="max-w-7xl mx-auto">
        <div className="mb-8">
          <h1 className="text-3xl font-bold text-foreground">同花顺行业数据</h1>
          <p className="text-muted-foreground mt-2">共 {sectors.length} 个行业</p>
        </div>

        <div className="grid grid-cols-2 sm:grid-cols-3 md:grid-cols-4 lg:grid-cols-5 xl:grid-cols-6 gap-4">
          {sectors.map((sector) => (
            <Link
              key={sector.id}
              href={`/industry/${sector.code}`}
              className="group p-4 rounded-lg border border-border bg-card hover:bg-accent hover:border-accent-foreground transition-all duration-200"
            >
              <div className="text-sm font-medium text-foreground group-hover:text-accent-foreground">
                {sector.name}
              </div>
              <div className="text-xs text-muted-foreground mt-1">
                {sector.code}
              </div>
            </Link>
          ))}
        </div>
      </div>
    </div>
  );
}
