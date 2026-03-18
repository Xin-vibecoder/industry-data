import { NextResponse } from 'next/server';
import { createClient } from '@supabase/supabase-js';

const supabaseUrl = process.env.COZE_SUPABASE_URL!;
const supabaseKey = process.env.COZE_SUPABASE_ANON_KEY!;

const supabase = createClient(supabaseUrl, supabaseKey);

export async function GET() {
  try {
    // 获取所有行业数据
    const { data, error } = await supabase
      .from('industry_daily_data')
      .select('sector_code, trade_date, close_price')
      .order('trade_date', { ascending: false });

    if (error) {
      return NextResponse.json({ error: error.message }, { status: 500 });
    }

    return NextResponse.json(data);
  } catch (error) {
    console.error('Failed to fetch all industries data:', error);
    return NextResponse.json(
      { error: 'Failed to fetch all industries data' },
      { status: 500 }
    );
  }
}
