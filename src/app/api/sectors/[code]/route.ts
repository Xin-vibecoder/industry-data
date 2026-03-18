import { NextResponse } from 'next/server';
import { createClient } from '@supabase/supabase-js';

const supabaseUrl = process.env.COZE_SUPABASE_URL!;
const supabaseKey = process.env.COZE_SUPABASE_ANON_KEY!;

const supabase = createClient(supabaseUrl, supabaseKey);

export async function GET(
  request: Request,
  { params }: { params: Promise<{ code: string }> }
) {
  try {
    const { code } = await params;

    // 获取行业每日数据
    const { data: dailyData, error: dailyError } = await supabase
      .from('industry_daily_data')
      .select('*')
      .eq('sector_code', code)
      .order('trade_date', { ascending: false });

    if (dailyError) {
      return NextResponse.json({ error: dailyError.message }, { status: 500 });
    }

    // 获取排名数据
    const { data: rankingsData, error: rankingsError } = await supabase
      .from('industry_rankings')
      .select('*')
      .eq('sector_code', code)
      .order('trade_date', { ascending: false });

    if (rankingsError) {
      return NextResponse.json({ error: rankingsError.message }, { status: 500 });
    }

    // 创建排名数据映射
    const rankingsMap: { [date: string]: any } = {};
    (rankingsData || []).forEach((row: any) => {
      rankingsMap[row.trade_date] = row;
    });

    // 合并数据
    const mergedData = (dailyData || []).map((row: any) => {
      const ranking = rankingsMap[row.trade_date] || {};
      return {
        ...row,
        daily_change: ranking.daily_change || null,
        five_day_change: ranking.five_day_change || null,
        twenty_day_change: ranking.twenty_day_change || null,
        five_day_rank: ranking.five_day_rank || null,
        twenty_day_rank: ranking.twenty_day_rank || null,
      };
    });

    return NextResponse.json(mergedData);
  } catch (error) {
    return NextResponse.json(
      { error: 'Failed to fetch industry data' },
      { status: 500 }
    );
  }
}
