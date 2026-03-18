'use client';

import RankingChart from './RankingChart';

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

interface IndustryDataDisplayProps {
  data: IndustryData[];
  name: string;
  code: string;
}

export default function IndustryDataDisplay({ data, name, code }: IndustryDataDisplayProps) {
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

  const formatChange = (change: number | null): string => {
    if (change === null) return '-';
    const sign = change > 0 ? '+' : '';
    return `${sign}${change.toFixed(2)}%`;
  };

  const getChangeColorClass = (change: number | null): string => {
    if (change === null) return 'text-muted-foreground';
    if (change > 0) return 'text-red-600 dark:text-red-400';
    if (change < 0) return 'text-green-600 dark:text-green-400';
    return 'text-muted-foreground';
  };

  // 提取最近60天的排名数据用于图表
  const chartData = data.slice(0, 60).map(row => ({
    trade_date: row.trade_date,
    five_day_rank: row.five_day_rank,
    twenty_day_rank: row.twenty_day_rank,
  })).reverse(); // 反转使日期从左到右递增

  return (
    <>
      {/* 趋势图 */}
      <RankingChart data={chartData} />

      {/* 数据表格 */}
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
                <th className="px-4 py-3 text-right text-sm font-semibold text-foreground">涨跌幅</th>
                <th className="px-4 py-3 text-right text-sm font-semibold text-foreground">五日涨跌</th>
                <th className="px-4 py-3 text-right text-sm font-semibold text-foreground">五日排名</th>
                <th className="px-4 py-3 text-right text-sm font-semibold text-foreground">二十日涨跌</th>
                <th className="px-4 py-3 text-right text-sm font-semibold text-foreground">二十日排名</th>
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
                  <td className={`px-4 py-3 text-sm text-right tabular-nums font-medium ${getChangeColorClass(row.daily_change)}`}>
                    {formatChange(row.daily_change)}
                  </td>
                  <td className={`px-4 py-3 text-sm text-right tabular-nums font-medium ${getChangeColorClass(row.five_day_change)}`}>
                    {formatChange(row.five_day_change)}
                  </td>
                  <td className="px-4 py-3 text-sm text-muted-foreground text-right tabular-nums">
                    {row.five_day_rank !== null ? `${row.five_day_rank}/90` : '-'}
                  </td>
                  <td className={`px-4 py-3 text-sm text-right tabular-nums font-medium ${getChangeColorClass(row.twenty_day_change)}`}>
                    {formatChange(row.twenty_day_change)}
                  </td>
                  <td className="px-4 py-3 text-sm text-muted-foreground text-right tabular-nums">
                    {row.twenty_day_rank !== null ? `${row.twenty_day_rank}/90` : '-'}
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
    </>
  );
}
