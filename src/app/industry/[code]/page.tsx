import type { Metadata } from 'next';
import Link from 'next/link';
import { notFound } from 'next/navigation';
import IndustryDataDisplay from '@/components/IndustryDataDisplay';

interface IndustryData {
  id: number;
  sector_code: string;
  trade_date: string;
  open_price: number;
  high_price: number;
  low_price: number;
  close_price: number;
  volume: number;
  amount: number;
  created_at: string;
  daily_change: number | null;
  five_day_change: number | null;
  twenty_day_change: number | null;
  five_day_rank: number | null;
  twenty_day_rank: number | null;
}

interface Sector {
  id: number;
  name: string;
  code: string;
}

async function getSectorName(code: string): Promise<string> {
  const res = await fetch(`${process.env.NEXT_PUBLIC_API_URL || 'http://localhost:5000'}/api/sectors`, {
    cache: 'no-store',
  });
  
  if (!res.ok) {
    return code;
  }
  
  const sectors: Sector[] = await res.json();
  const sector = sectors.find(s => s.code === code);
  return sector?.name || code;
}

async function getIndustryData(code: string): Promise<IndustryData[]> {
  const res = await fetch(`${process.env.NEXT_PUBLIC_API_URL || 'http://localhost:5000'}/api/sectors/${code}`, {
    cache: 'no-store',
  });
  
  if (!res.ok) {
    return [];
  }
  
  return res.json();
}

interface PageProps {
  params: Promise<{
    code: string;
  }>;
}

export async function generateMetadata({ params }: PageProps): Promise<Metadata> {
  const { code } = await params;
  const name = await getSectorName(code);
  return {
    title: `${name} - 行业数据`,
  };
}

export default async function IndustryPage({ params }: PageProps) {
  const { code } = await params;
  const data = await getIndustryData(code);
  const name = await getSectorName(code);
  
  if (data.length === 0) {
    notFound();
  }

  return (
    <div className="min-h-screen bg-background">
      <div className="max-w-7xl mx-auto px-4 py-6 sm:px-6 lg:px-8">
        {/* 面包屑导航 */}
        <div className="mb-6">
          <Link 
            href="/" 
            className="text-sm text-muted-foreground hover:text-foreground transition-colors"
          >
            ← 返回首页
          </Link>
        </div>

        {/* 页面标题 */}
        <div className="mb-8">
          <h1 className="text-3xl font-bold text-foreground mb-2">{name}</h1>
          <p className="text-muted-foreground">行业代码: {code}</p>
        </div>

        {/* 使用客户端组件展示数据和图表 */}
        <IndustryDataDisplay data={data} name={name} code={code} />
      </div>
    </div>
  );
}
