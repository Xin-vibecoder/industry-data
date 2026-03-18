'use client';

import {
  LineChart,
  Line,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  Legend,
  ResponsiveContainer,
} from 'recharts';

interface RankingData {
  trade_date: string;
  five_day_rank: number | null;
  twenty_day_rank: number | null;
}

interface RankingChartProps {
  data: RankingData[];
}

export default function RankingChart({ data }: RankingChartProps) {
  // 格式化日期显示（只显示月-日）
  const formatXAxis = (date: string) => {
    const parts = date.split('-');
    return parts.length >= 3 ? `${parts[1]}-${parts[2]}` : date;
  };

  // 格式化Tooltip
  // eslint-disable-next-line @typescript-eslint/no-explicit-any
  const formatTooltip = (value: any, name: string): [string, string] => {
    if (value === null || value === undefined) return ['-', name];
    return [`排名: ${value}`, name === 'five_day_rank' ? '五日排名' : '二十日排名'];
  };

  return (
    <div className="w-full bg-card rounded-lg border border-border p-4 mb-6">
      <h2 className="text-lg font-semibold text-foreground mb-4">排名趋势（最近60天）</h2>
      <div className="h-[300px]">
        <ResponsiveContainer width="100%" height="100%">
          <LineChart
            data={data}
            margin={{
              top: 10,
              right: 30,
              left: 0,
              bottom: 0,
            }}
          >
            <CartesianGrid strokeDasharray="3 3" stroke="hsl(var(--border))" />
            <XAxis 
              dataKey="trade_date" 
              tickFormatter={formatXAxis}
              stroke="hsl(var(--muted-foreground))"
              fontSize={12}
              tickLine={false}
              axisLine={{ stroke: 'hsl(var(--border))' }}
            />
            <YAxis 
              domain={[1, 90]}
              reversed={true}
              stroke="hsl(var(--muted-foreground))"
              fontSize={12}
              tickLine={false}
              axisLine={{ stroke: 'hsl(var(--border))' }}
              label={{ 
                value: '排名', 
                angle: -90, 
                position: 'insideLeft',
                style: { fill: 'hsl(var(--muted-foreground))' }
              }}
            />
            <Tooltip 
              formatter={formatTooltip}
              labelFormatter={(label) => `日期: ${label}`}
              contentStyle={{
                backgroundColor: 'hsl(var(--card))',
                border: '1px solid hsl(var(--border))',
                borderRadius: '6px',
              }}
            />
            <Legend 
              formatter={(value) => value === 'five_day_rank' ? '五日排名' : '二十日排名'}
            />
            <Line
              type="monotone"
              dataKey="five_day_rank"
              stroke="#ef4444"
              strokeWidth={2}
              dot={false}
              activeDot={{ r: 4 }}
              name="five_day_rank"
              connectNulls={false}
            />
            <Line
              type="monotone"
              dataKey="twenty_day_rank"
              stroke="#3b82f6"
              strokeWidth={2}
              dot={false}
              activeDot={{ r: 4 }}
              name="twenty_day_rank"
              connectNulls={false}
            />
          </LineChart>
        </ResponsiveContainer>
      </div>
    </div>
  );
}
