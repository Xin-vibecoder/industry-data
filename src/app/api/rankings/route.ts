import { NextResponse } from 'next/server';
import { createClient } from '@supabase/supabase-js';

const supabaseUrl = process.env.COZE_SUPABASE_URL!;
const supabaseKey = process.env.COZE_SUPABASE_ANON_KEY!;

const supabase = createClient(supabaseUrl, supabaseKey);

interface IndustryData {
  id: number;
  sector_code: string;
  trade_date: string;
  close_price: number;
}

interface RankingData {
  [date: string]: {
    [sectorCode: string]: {
      fiveDayRank: number | null;
      twentyDayRank: number | null;
    };
  };
}

// 计算涨跌幅
function calculateChange(currentClose: number, previousClose: number | null): number | null {
  if (previousClose === null || previousClose === 0) return null;
  return ((currentClose - previousClose) / previousClose) * 100;
}

export async function GET() {
  try {
    // 获取所有行业数据
    const { data: allData, error } = await supabase
      .from('industry_daily_data')
      .select('id, sector_code, trade_date, close_price')
      .order('trade_date', { ascending: false });

    if (error) {
      return NextResponse.json({ error: error.message }, { status: 500 });
    }

    if (!allData || allData.length === 0) {
      return NextResponse.json({});
    }

    // 按行业代码分组
    const dataBySector: { [code: string]: IndustryData[] } = {};
    allData.forEach((row: IndustryData) => {
      if (!dataBySector[row.sector_code]) {
        dataBySector[row.sector_code] = [];
      }
      dataBySector[row.sector_code].push(row);
    });

    // 按日期分组
    const dataByDate: { [date: string]: IndustryData[] } = {};
    allData.forEach((row: IndustryData) => {
      if (!dataByDate[row.trade_date]) {
        dataByDate[row.trade_date] = [];
      }
      dataByDate[row.trade_date].push(row);
    });

    // 获取所有日期（倒序）
    const allDates = Object.keys(dataByDate).sort().reverse();

    // 为每个行业计算涨跌幅
    const sectorChanges: { [code: string]: { [date: string]: { fiveDay: number | null; twentyDay: number | null } } } = {};
    
    Object.keys(dataBySector).forEach(code => {
      const sectorData = dataBySector[code];
      sectorChanges[code] = {};

      sectorData.forEach((row, index) => {
        // 五日涨跌
        const fiveDayClose = index < sectorData.length - 5 ? sectorData[index + 5].close_price : null;
        const fiveDayChange = calculateChange(row.close_price, fiveDayClose);

        // 二十日涨跌
        const twentyDayClose = index < sectorData.length - 20 ? sectorData[index + 20].close_price : null;
        const twentyDayChange = calculateChange(row.close_price, twentyDayClose);

        sectorChanges[code][row.trade_date] = {
          fiveDay: fiveDayChange,
          twentyDay: twentyDayChange
        };
      });
    });

    // 计算每个日期的排名
    const rankings: RankingData = {};

    allDates.forEach(date => {
      rankings[date] = {};

      // 获取该日期所有行业的涨跌幅
      const fiveDayChanges: { code: string; change: number | null }[] = [];
      const twentyDayChanges: { code: string; change: number | null }[] = [];

      dataByDate[date].forEach((row: IndustryData) => {
        const changes = sectorChanges[row.sector_code]?.[date];
        if (changes) {
          fiveDayChanges.push({ code: row.sector_code, change: changes.fiveDay });
          twentyDayChanges.push({ code: row.sector_code, change: changes.twentyDay });
        }
      });

      // 排序并计算排名（涨幅越大，排名越小，即排名数字越小）
      // 过滤掉null值，只对有效值排序
      const sortedFiveDay = fiveDayChanges
        .filter(item => item.change !== null)
        .sort((a, b) => (b.change as number) - (a.change as number));
      
      const sortedTwentyDay = twentyDayChanges
        .filter(item => item.change !== null)
        .sort((a, b) => (b.change as number) - (a.change as number));

      // 创建排名映射
      fiveDayChanges.forEach(item => {
        if (item.change !== null) {
          const rank = sortedFiveDay.findIndex(s => s.code === item.code) + 1;
          rankings[date][item.code] = {
            ...rankings[date][item.code],
            fiveDayRank: rank > 0 ? rank : null
          };
        } else {
          rankings[date][item.code] = {
            ...rankings[date][item.code],
            fiveDayRank: null
          };
        }
      });

      twentyDayChanges.forEach(item => {
        if (item.change !== null) {
          const rank = sortedTwentyDay.findIndex(s => s.code === item.code) + 1;
          rankings[date][item.code] = {
            ...rankings[date][item.code],
            twentyDayRank: rank > 0 ? rank : null
          };
        } else {
          rankings[date][item.code] = {
            ...rankings[date][item.code],
            twentyDayRank: rankings[date][item.code]?.twentyDayRank || null
          };
        }
      });
    });

    return NextResponse.json(rankings);
  } catch (error) {
    console.error('Error calculating rankings:', error);
    return NextResponse.json(
      { error: 'Failed to calculate rankings' },
      { status: 500 }
    );
  }
}
