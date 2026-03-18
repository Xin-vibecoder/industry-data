import { NextResponse } from 'next/server';
import { createClient } from '@supabase/supabase-js';

const supabaseUrl = process.env.COZE_SUPABASE_URL!;
const supabaseKey = process.env.COZE_SUPABASE_ANON_KEY!;

const supabase = createClient(supabaseUrl, supabaseKey);

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
    // 从数据库读取排名数据
    const { data, error } = await supabase
      .from('industry_rankings')
      .select('*')
      .order('trade_date', { ascending: false });

    if (error) {
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
    console.error('Error fetching rankings:', error);
    return NextResponse.json(
      { error: 'Failed to fetch rankings' },
      { status: 500 }
    );
  }
}
