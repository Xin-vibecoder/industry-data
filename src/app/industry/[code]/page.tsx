import type { Metadata } from 'next';
import Link from 'next/link';
import { notFound } from 'next/navigation';

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

export async function generateMetadata({ params }: { params: Promise<{ code: string }> }): Promise<Metadata> {
  const { code } = await params;
  const name = await getSectorName(code);
  
  return {
    title: `${name} - 行业数据`,
    description: `查看${name}行业的历史数据`,
  };
}

export default async function IndustryPage({ params }: { params: Promise<{ code: string }> }) {
  const { code } = await params;
  const name = await getSectorName(code);
  const data = await getIndustryData(code);

  if (data.length === 0) {
    notFound();
  }

  const formatNumber = (num: number, decimals: number = 2): string => {
    return num.toLocaleString('zh-CN', {
      minimumFractionDigits: decimals,
      maximumFractionDigits: decimals,
    });
  };

  const formatVolume = (num: number): string => {
    if (num >= 100000000) {
      return `${(num / 100000000).toFixed(2)}亿`;
    } else if (num >= 10000) {
      return `${(num / 10000).toFixed(2)}万`;
    }
    return num.toLocaleString('zh-CN');
  };

  return (
    <div className="min-h-screen bg-background p-8">
      <div className="max-w-7xl mx-auto">
        <div className="mb-6">
          <Link
            href="/"
            className="text-sm text-muted-foreground hover:text-foreground transition-colors"
          >
            ← 返回行业列表
          </Link>
        </div>

        <div className="mb-8">
          <h1 className="text-3xl font-bold text-foreground">{name}</h1>
          <p className="text-muted-foreground mt-2">
            行业代码: {code} | 共 {data.length} 条历史数据
          </p>
        </div>

        <div className="rounded-lg border border-border bg-card overflow-hidden">
          <div className="overflow-x-auto">
            <table className="w-full">
              <thead>
                <tr className="border-b border-border bg-muted/50">
                  <th className="px-4 py-3 text-left text-sm font-semibold text-foreground">日期</th>
                  <th className="px-4 py-3 text-right text-sm font-semibold text-foreground">开盘价</th>
                  <th className="px-4 py-3 text-right text-sm font-semibold text-foreground">最高价</th>
                  <th className="px-4 py-3 text-right text-sm font-semibold text-foreground">最低价</th>
                  <th className="px-4 py-3 text-right text-sm font-semibold text-foreground">收盘价</th>
                  <th className="px-4 py-3 text-right text-sm font-semibold text-foreground">成交量</th>
                  <th className="px-4 py-3 text-right text-sm font-semibold text-foreground">成交额</th>
                </tr>
              </thead>
              <tbody>
                {data.map((row, index) => (
                  <tr
                    key={row.id}
                    className={`border-b border-border hover:bg-muted/30 transition-colors ${
                      index % 2 === 0 ? 'bg-background' : 'bg-muted/20'
                    }`}
                  >
                    <td className="px-4 py-3 text-sm text-foreground font-medium">
                      {row.trade_date}
                    </td>
                    <td className="px-4 py-3 text-sm text-foreground text-right tabular-nums">
                      {formatNumber(row.open_price)}
                    </td>
                    <td className="px-4 py-3 text-sm text-red-600 dark:text-red-400 text-right tabular-nums font-medium">
                      {formatNumber(row.high_price)}
                    </td>
                    <td className="px-4 py-3 text-sm text-green-600 dark:text-green-400 text-right tabular-nums font-medium">
                      {formatNumber(row.low_price)}
                    </td>
                    <td className="px-4 py-3 text-sm text-foreground text-right tabular-nums font-medium">
                      {formatNumber(row.close_price)}
                    </td>
                    <td className="px-4 py-3 text-sm text-muted-foreground text-right tabular-nums">
                      {formatVolume(row.volume)}
                    </td>
                    <td className="px-4 py-3 text-sm text-muted-foreground text-right tabular-nums">
                      {formatVolume(row.amount)}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>

        <div className="mt-4 text-xs text-muted-foreground">
          数据从2024年1月1日至今，按时间倒序排列
        </div>
      </div>
    </div>
  );
}
