/**
 * 同花顺行业数据增量更新服务
 * 使用 Node.js 原生 HTTP 请求，可在生产环境运行
 */

import { getSupabaseClient } from '@/storage/database/supabase-client';

// 行业数据接口
interface IndustryDailyData {
  sector_code: string;
  trade_date: string;
  open_price: number;
  high_price: number;
  low_price: number;
  close_price: number;
  volume: number;
  amount: number;
}

interface SectorInfo {
  code: string;
  name: string;
}

interface RankingRecord {
  sector_code: string;
  trade_date: string;
  daily_change: number | null;
  five_day_change: number | null;
  twenty_day_change: number | null;
  five_day_rank: number | null;
  twenty_day_rank: number | null;
}

// 更新结果
interface UpdateResult {
  success: boolean;
  message: string;
  sectorsUpdated: number;
  recordsInserted: number;
  rankingsUpdated: number;
  errors: string[];
  duration: number;
}

/**
 * 从数据库获取行业列表
 */
async function getSectorsFromDB(): Promise<SectorInfo[]> {
  const supabase = getSupabaseClient();
  const { data, error } = await supabase
    .from('industry_sectors')
    .select('code, name')
    .order('name');
  
  if (error) {
    throw new Error(`Failed to fetch sectors: ${error.message}`);
  }
  
  return data || [];
}

/**
 * 从东方财富获取行业板块行情数据
 */
async function fetchSectorQuote(sectorCode: string): Promise<{
  price: number;
  change: number;
  changePercent: number;
  volume: number;
  amount: number;
  high: number;
  low: number;
  open: number;
} | null> {
  try {
    // 东方财富行业板块接口
    const url = `https://push2.eastmoney.com/api/qt/stock/get?secid=90.${sectorCode}&fields=f43,f44,f45,f46,f47,f48,f50,f51,f52,f58,f60,f169,f170`;
    
    const response = await fetch(url, {
      headers: {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
        'Referer': 'https://quote.eastmoney.com/',
      },
    });
    
    if (!response.ok) {
      return null;
    }
    
    const result = await response.json();
    
    if (!result.data) {
      return null;
    }
    
    const d = result.data;
    
    return {
      price: (d.f43 || 0) / 100,  // 最新价
      high: (d.f44 || 0) / 100,   // 最高价
      low: (d.f45 || 0) / 100,    // 最低价
      open: (d.f46 || 0) / 100,   // 开盘价
      volume: d.f47 || 0,         // 成交量
      amount: (d.f48 || 0) / 100, // 成交额
      change: (d.f169 || 0) / 100, // 涨跌额
      changePercent: (d.f170 || 0) / 100, // 涨跌幅
    };
  } catch (error) {
    console.error(`[Updater] Failed to fetch quote for ${sectorCode}:`, error);
    return null;
  }
}

/**
 * 获取最近N个交易日的日期
 */
function getRecentTradeDates(days: number): string[] {
  const dates: string[] = [];
  const today = new Date();
  
  for (let i = 0; i < days * 2 && dates.length < days; i++) {
    const d = new Date(today);
    d.setDate(d.getDate() - i);
    
    // 跳过周末
    const dayOfWeek = d.getDay();
    if (dayOfWeek !== 0 && dayOfWeek !== 6) {
      dates.push(d.toISOString().split('T')[0]);
    }
  }
  
  return dates;
}

/**
 * 获取今天的日期字符串
 */
function getTodayDate(): string {
  return new Date().toISOString().split('T')[0];
}

/**
 * 检查今天是否为交易日（简单判断：排除周末）
 */
function isTradingDay(): boolean {
  const dayOfWeek = new Date().getDay();
  return dayOfWeek !== 0 && dayOfWeek !== 6;
}

/**
 * 插入每日数据
 */
async function insertDailyData(data: IndustryDailyData): Promise<boolean> {
  const supabase = getSupabaseClient();
  
  // 先删除可能存在的重复记录
  await supabase
    .from('industry_daily_data')
    .delete()
    .eq('sector_code', data.sector_code)
    .eq('trade_date', data.trade_date);
  
  // 插入新记录
  const { error } = await supabase
    .from('industry_daily_data')
    .insert(data);
  
  if (error) {
    console.error(`[Updater] Failed to insert daily data:`, error);
    return false;
  }
  
  return true;
}

/**
 * 计算并存储排名
 */
async function calculateAndStoreRankings(tradeDate: string): Promise<number> {
  const supabase = getSupabaseClient();
  
  console.log(`[Updater] Calculating rankings for ${tradeDate}`);
  
  // 1. 获取该日期所有行业的收盘价
  const { data: todayData, error: todayError } = await supabase
    .from('industry_daily_data')
    .select('sector_code, close_price')
    .eq('trade_date', tradeDate);
  
  if (todayError || !todayData || todayData.length === 0) {
    console.error(`[Updater] No data found for ${tradeDate}`);
    return 0;
  }
  
  // 2. 获取前一个交易日的日期
  const prevDate = new Date(tradeDate);
  prevDate.setDate(prevDate.getDate() - 1);
  
  // 跳过周末
  while (prevDate.getDay() === 0 || prevDate.getDay() === 6) {
    prevDate.setDate(prevDate.getDate() - 1);
  }
  const prevDateStr = prevDate.toISOString().split('T')[0];
  
  // 3. 获取前一日数据
  const { data: prevData } = await supabase
    .from('industry_daily_data')
    .select('sector_code, close_price')
    .eq('trade_date', prevDateStr);
  
  // 创建映射
  const prevPriceMap: { [code: string]: number } = {};
  (prevData || []).forEach(row => {
    prevPriceMap[row.sector_code] = row.close_price;
  });
  
  // 4. 计算涨跌幅
  const rankings: { code: string; dailyChange: number | null }[] = [];
  
  for (const row of todayData) {
    const prevClose = prevPriceMap[row.sector_code];
    let dailyChange: number | null = null;
    
    if (prevClose && prevClose > 0) {
      dailyChange = ((row.close_price - prevClose) / prevClose) * 100;
    }
    
    rankings.push({
      code: row.sector_code,
      dailyChange,
    });
  }
  
  // 5. 按涨跌幅排序（降序）
  rankings.sort((a, b) => {
    if (a.dailyChange === null) return 1;
    if (b.dailyChange === null) return -1;
    return b.dailyChange - a.dailyChange;
  });
  
  // 6. 保存排名
  let count = 0;
  for (let i = 0; i < rankings.length; i++) {
    const rank = i + 1;
    const item = rankings[i];
    
    // 获取五日和二十日前的数据计算累计涨跌幅
    let fiveDayChange: number | null = null;
    let twentyDayChange: number | null = null;
    
    // 五日前
    const fiveDaysAgo = new Date(tradeDate);
    for (let j = 0; j < 5; j++) {
      fiveDaysAgo.setDate(fiveDaysAgo.getDate() - 1);
      while (fiveDaysAgo.getDay() === 0 || fiveDaysAgo.getDay() === 6) {
        fiveDaysAgo.setDate(fiveDaysAgo.getDate() - 1);
      }
    }
    
    const { data: fiveDayData } = await supabase
      .from('industry_daily_data')
      .select('close_price')
      .eq('sector_code', item.code)
      .eq('trade_date', fiveDaysAgo.toISOString().split('T')[0])
      .single();
    
    if (fiveDayData?.close_price && todayData.find(d => d.sector_code === item.code)) {
      const currentClose = todayData.find(d => d.sector_code === item.code)!.close_price;
      if (fiveDayData.close_price > 0) {
        fiveDayChange = ((currentClose - fiveDayData.close_price) / fiveDayData.close_price) * 100;
      }
    }
    
    // 二十日前
    const twentyDaysAgo = new Date(tradeDate);
    for (let j = 0; j < 20; j++) {
      twentyDaysAgo.setDate(twentyDaysAgo.getDate() - 1);
      while (twentyDaysAgo.getDay() === 0 || twentyDaysAgo.getDay() === 6) {
        twentyDaysAgo.setDate(twentyDaysAgo.getDate() - 1);
      }
    }
    
    const { data: twentyDayData } = await supabase
      .from('industry_daily_data')
      .select('close_price')
      .eq('sector_code', item.code)
      .eq('trade_date', twentyDaysAgo.toISOString().split('T')[0])
      .single();
    
    if (twentyDayData?.close_price && todayData.find(d => d.sector_code === item.code)) {
      const currentClose = todayData.find(d => d.sector_code === item.code)!.close_price;
      if (twentyDayData.close_price > 0) {
        twentyDayChange = ((currentClose - twentyDayData.close_price) / twentyDayData.close_price) * 100;
      }
    }
    
    const rankingRecord: RankingRecord = {
      sector_code: item.code,
      trade_date: tradeDate,
      daily_change: item.dailyChange,
      five_day_change: fiveDayChange,
      twenty_day_change: twentyDayChange,
      five_day_rank: rank,
      twenty_day_rank: rank,
    };
    
    // 删除旧记录
    await supabase
      .from('industry_rankings')
      .delete()
      .eq('sector_code', item.code)
      .eq('trade_date', tradeDate);
    
    // 插入新记录
    const { error } = await supabase
      .from('industry_rankings')
      .insert(rankingRecord);
    
    if (!error) {
      count++;
    }
  }
  
  console.log(`[Updater] Stored ${count} rankings for ${tradeDate}`);
  return count;
}

/**
 * 执行增量更新
 */
export async function runIncrementalUpdate(): Promise<UpdateResult> {
  const startTime = Date.now();
  const errors: string[] = [];
  let sectorsUpdated = 0;
  let recordsInserted = 0;
  let rankingsUpdated = 0;
  
  console.log('[Updater] Starting incremental update...');
  
  try {
    const supabase = getSupabaseClient();
    
    // 检查是否为交易日
    if (!isTradingDay()) {
      return {
        success: false,
        message: 'Today is not a trading day (weekend)',
        sectorsUpdated: 0,
        recordsInserted: 0,
        rankingsUpdated: 0,
        errors: [],
        duration: Date.now() - startTime,
      };
    }
    
    const today = getTodayDate();
    console.log(`[Updater] Today: ${today}`);
    
    // 1. 获取行业列表
    const sectors = await getSectorsFromDB();
    console.log(`[Updater] Found ${sectors.length} sectors`);
    
    if (sectors.length === 0) {
      return {
        success: false,
        message: 'No sectors found in database',
        sectorsUpdated: 0,
        recordsInserted: 0,
        rankingsUpdated: 0,
        errors: ['Empty sector list'],
        duration: Date.now() - startTime,
      };
    }
    
    // 2. 获取每个行业的今日行情
    console.log('[Updater] Fetching quotes...');
    
    for (const sector of sectors) {
      try {
        const quote = await fetchSectorQuote(sector.code);
        
        if (quote && quote.price > 0) {
          const dailyData: IndustryDailyData = {
            sector_code: sector.code,
            trade_date: today,
            open_price: quote.open,
            high_price: quote.high,
            low_price: quote.low,
            close_price: quote.price,
            volume: quote.volume,
            amount: quote.amount,
          };
          
          const inserted = await insertDailyData(dailyData);
          if (inserted) {
            sectorsUpdated++;
            recordsInserted++;
          }
        }
        
        // 延迟避免请求过快
        await new Promise(resolve => setTimeout(resolve, 100));
        
      } catch (error) {
        const errMsg = `Failed to update ${sector.name}: ${error}`;
        console.error(`[Updater] ${errMsg}`);
        errors.push(errMsg);
      }
    }
    
    console.log(`[Updater] Updated ${sectorsUpdated} sectors`);
    
    // 3. 计算排名
    if (recordsInserted > 0) {
      rankingsUpdated = await calculateAndStoreRankings(today);
    }
    
    const duration = Date.now() - startTime;
    console.log(`[Updater] Completed in ${duration}ms`);
    
    return {
      success: true,
      message: `Incremental update completed. Updated ${sectorsUpdated} sectors, ${recordsInserted} records, ${rankingsUpdated} rankings.`,
      sectorsUpdated,
      recordsInserted,
      rankingsUpdated,
      errors,
      duration,
    };
    
  } catch (error) {
    const errMsg = error instanceof Error ? error.message : 'Unknown error';
    console.error('[Updater] Update failed:', errMsg);
    errors.push(errMsg);
    
    return {
      success: false,
      message: `Update failed: ${errMsg}`,
      sectorsUpdated,
      recordsInserted,
      rankingsUpdated,
      errors,
      duration: Date.now() - startTime,
    };
  }
}
