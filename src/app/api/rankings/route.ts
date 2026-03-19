import { NextResponse } from 'next/server';
import { getSupabaseClient } from '@/storage/database/supabase-client';

interface RankingRow {
  id: number;
  sector_code: string;
  trade_date: string;
  daily_change: number | null;
  five_day_change: number | null;
  twenty_day_change: number | null;
  five_day_rank: number | null;
  twenty_day_rank: number | null;
}

interface RankingData {
  [date: string]: {
    [sectorCode: string]: {
      fiveDayRank: number | null;
      twentyDayRank: number | null;
    };
  };
}

export async function GET() {
  try {
    const supabase = getSupabaseClient();
    
    // 从数据库读取排名数据
    const { data, error } = await supabase
      .from('industry_rankings')
      .select('*')
      .order('trade_date', { ascending: false });

    if (error) {
      console.error('Supabase query error:', error);
      return NextResponse.json({ error: error.message }, { status: 500 });
    }

    if (!data || data.length === 0) {
      return NextResponse.json({});
    }

    // 转换为原来的格式
    const rankings: RankingData = {};

    data.forEach((row: RankingRow) => {
      if (!rankings[row.trade_date]) {
        rankings[row.trade_date] = {};
      }

      rankings[row.trade_date][row.sector_code] = {
        fiveDayRank: row.five_day_rank,
        twentyDayRank: row.twenty_day_rank,
      };
    });

    return NextResponse.json(rankings);
  } catch (error) {
    console.error('API error:', error);
    const message = error instanceof Error ? error.message : 'Failed to fetch rankings';
    return NextResponse.json({ error: message }, { status: 500 });
  }
}
