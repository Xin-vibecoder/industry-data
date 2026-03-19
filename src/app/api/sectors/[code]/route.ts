import { NextResponse } from 'next/server';
import { getSupabaseClient } from '@/storage/database/supabase-client';

export async function GET(
  request: Request,
  { params }: { params: Promise<{ code: string }> }
) {
  try {
    const supabase = getSupabaseClient();
    const { code } = await params;

    // 获取行业每日数据
    const { data: dailyData, error: dailyError } = await supabase
      .from('industry_daily_data')
      .select('*')
      .eq('sector_code', code)
      .order('trade_date', { ascending: false });

    if (dailyError) {
      console.error('Supabase daily data query error:', dailyError);
      return NextResponse.json({ error: dailyError.message }, { status: 500 });
    }

    // 获取排名数据
    const { data: rankingsData, error: rankingsError } = await supabase
      .from('industry_rankings')
      .select('*')
      .eq('sector_code', code)
      .order('trade_date', { ascending: false });

    if (rankingsError) {
      console.error('Supabase rankings query error:', rankingsError);
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
    console.error('API error:', error);
    const message = error instanceof Error ? error.message : 'Failed to fetch industry data';
    return NextResponse.json({ error: message }, { status: 500 });
  }
}
