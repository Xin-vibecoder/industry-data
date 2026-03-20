/**
 * 同花顺行业数据增量更新服务
 * 使用东方财富历史K线接口获取数据
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
 * 从东方财富获取行业板块历史K线数据
 * 使用日K线接口获取最近几天的数据
 */
async function fetchSectorKline(sectorCode: string, days: number = 3): Promise<IndustryDailyData[]> {
  try {
    const endDate = new Date();
    const startDate = new Date();
    startDate.setDate(startDate.getDate() - days * 3); // 多获取几天确保覆盖
    
    const formatDate = (d: Date) => {
      const year = d.getFullYear();
      const month = String(d.getMonth() + 1).padStart(2, '0');
      const day = String(d.getDate()).padStart(2, '0');
      return `${year}${month}${day}`;
    };
    
    // 东方财富日K线接口 (secid=90 表示板块指数)
    const url = `https://push2his.eastmoney.com/api/qt/stock/kline/get?secid=90.${sectorCode}&fields1=f1,f2,f3,f4,f5,f6&fields2=f51,f52,f53,f54,f55,f56,f57&klt=101&fqt=1&beg=${formatDate(startDate)}&end=${formatDate(endDate)}`;
    
    const response = await fetch(url, {
      headers: {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
        'Referer': 'https://quote.eastmoney.com/',
      },
    });
    
    if (!response.ok) {
      return [];
    }
    
    const result = await response.json();
    
    if (!result.data?.klines) {
      return [];
    }
    
    const klines = result.data.klines as string[];
    
    // 计算需要获取的日期
    const recentDates: string[] = [];
    for (let i = 0; i < days * 2 && recentDates.length < days; i++) {
      const d = new Date();
      d.setDate(d.getDate() - i);
      // 跳过周末
      if (d.getDay() !== 0 && d.getDay() !== 6) {
        recentDates.push(d.toISOString().split('T')[0]);
      }
    }
    
    // 解析K线数据
    // 格式: 日期,开盘,收盘,最高,最低,成交量,成交额
    return klines
      .map((line: string) => {
        const parts = line.split(',');
        const dateStr = parts[0]; // 格式: YYYY-MM-DD
        
        if (!recentDates.includes(dateStr)) {
          return null;
        }
        
        return {
          sector_code: sectorCode,
          trade_date: dateStr,
          open_price: parseFloat(parts[1]) || 0,
          close_price: parseFloat(parts[2]) || 0,
          high_price: parseFloat(parts[3]) || 0,
          low_price: parseFloat(parts[4]) || 0,
          volume: parseInt(parts[5]) || 0,
          amount: parseFloat(parts[6]) || 0,
        };
      })
      .filter((item): item is IndustryDailyData => item !== null);
    
  } catch (error) {
    console.error(`[Updater] Failed to fetch kline for ${sectorCode}:`, error);
    return [];
  }
}

/**
 * 插入每日数据到数据库
 */
async function insertDailyData(data: IndustryDailyData[]): Promise<number> {
  if (data.length === 0) return 0;
  
  const supabase = getSupabaseClient();
  
  let inserted = 0;
  for (const item of data) {
    // 先删除已有数据
    await supabase
      .from('industry_daily_data')
      .delete()
      .eq('sector_code', item.sector_code)
      .eq('trade_date', item.trade_date);
    
    // 插入新数据
    const { error } = await supabase
      .from('industry_daily_data')
      .insert(item);
    
    if (!error) {
      inserted++;
    }
  }
  
  return inserted;
}

/**
 * 计算并存储排名
 */
async function calculateAndStoreRankings(): Promise<number> {
  const supabase = getSupabaseClient();
  
  // 获取最新数据的日期
  const { data: latestData } = await supabase
    .from('industry_daily_data')
    .select('trade_date')
    .order('trade_date', { ascending: false })
    .limit(1);
  
  if (!latestData || latestData.length === 0) {
    console.log('[Updater] No data found');
    return 0;
  }
  
  const tradeDate = latestData[0].trade_date;
  console.log(`[Updater] Calculating rankings for ${tradeDate}`);
  
  // 获取该日期所有行业的收盘价
  const { data: todayData } = await supabase
    .from('industry_daily_data')
    .select('sector_code, close_price')
    .eq('trade_date', tradeDate);
  
  if (!todayData || todayData.length === 0) {
    return 0;
  }
  
  // 获取前一个交易日
  const prevDate = new Date(tradeDate);
  do {
    prevDate.setDate(prevDate.getDate() - 1);
  } while (prevDate.getDay() === 0 || prevDate.getDay() === 6);
  const prevDateStr = prevDate.toISOString().split('T')[0];
  
  // 获取前一日数据
  const { data: prevData } = await supabase
    .from('industry_daily_data')
    .select('sector_code, close_price')
    .eq('trade_date', prevDateStr);
  
  const prevPriceMap: { [code: string]: number } = {};
  (prevData || []).forEach(row => {
    prevPriceMap[row.sector_code] = row.close_price;
  });
  
  // 计算涨跌幅
  const rankings: { code: string; dailyChange: number | null; closePrice: number }[] = [];
  
  for (const row of todayData) {
    const prevClose = prevPriceMap[row.sector_code];
    let dailyChange: number | null = null;
    
    if (prevClose && prevClose > 0) {
      dailyChange = ((row.close_price - prevClose) / prevClose) * 100;
    }
    
    rankings.push({
      code: row.sector_code,
      dailyChange,
      closePrice: row.close_price,
    });
  }
  
  // 按涨跌幅排序（降序）
  rankings.sort((a, b) => {
    if (a.dailyChange === null) return 1;
    if (b.dailyChange === null) return -1;
    return b.dailyChange - a.dailyChange;
  });
  
  // 计算五日和二十日涨跌幅的辅助函数
  const getChangeFromDaysAgo = async (code: string, days: number): Promise<number | null> => {
    const targetDate = new Date(tradeDate);
    let tradingDays = 0;
    while (tradingDays < days) {
      targetDate.setDate(targetDate.getDate() - 1);
      if (targetDate.getDay() !== 0 && targetDate.getDay() !== 6) {
        tradingDays++;
      }
    }
    
    const { data } = await supabase
      .from('industry_daily_data')
      .select('close_price')
      .eq('sector_code', code)
      .eq('trade_date', targetDate.toISOString().split('T')[0])
      .single();
    
    return data?.close_price || null;
  };
  
  // 保存排名
  let count = 0;
  for (let i = 0; i < rankings.length; i++) {
    const rank = i + 1;
    const item = rankings[i];
    
    // 计算五日和二十日涨跌幅
    let fiveDayChange: number | null = null;
    let twentyDayChange: number | null = null;
    
    const fiveDayAgoClose = await getChangeFromDaysAgo(item.code, 5);
    if (fiveDayAgoClose && fiveDayAgoClose > 0) {
      fiveDayChange = ((item.closePrice - fiveDayAgoClose) / fiveDayAgoClose) * 100;
    }
    
    const twentyDayAgoClose = await getChangeFromDaysAgo(item.code, 20);
    if (twentyDayAgoClose && twentyDayAgoClose > 0) {
      twentyDayChange = ((item.closePrice - twentyDayAgoClose) / twentyDayAgoClose) * 100;
    }
    
    // 删除旧记录
    await supabase
      .from('industry_rankings')
      .delete()
      .eq('sector_code', item.code)
      .eq('trade_date', tradeDate);
    
    // 插入新记录
    const { error } = await supabase
      .from('industry_rankings')
      .insert({
        sector_code: item.code,
        trade_date: tradeDate,
        daily_change: item.dailyChange,
        five_day_change: fiveDayChange,
        twenty_day_change: twentyDayChange,
        five_day_rank: rank,
        twenty_day_rank: rank,
      });
    
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
export async function runIncrementalUpdate(days: number = 2): Promise<UpdateResult> {
  const startTime = Date.now();
  const errors: string[] = [];
  let sectorsUpdated = 0;
  let recordsInserted = 0;
  let rankingsUpdated = 0;
  
  console.log(`[Updater] Starting incremental update for last ${days} days...`);
  
  try {
    // 1. 获取行业列表
    console.log('[Updater] Fetching sector list...');
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
    
    // 2. 获取每个行业的历史K线数据
    console.log('[Updater] Fetching kline data...');
    
    for (const sector of sectors) {
      try {
        const data = await fetchSectorKline(sector.code, days);
        
        if (data.length > 0) {
          const inserted = await insertDailyData(data);
          if (inserted > 0) {
            sectorsUpdated++;
            recordsInserted += inserted;
          }
        }
        
        // 延迟避免请求过快
        await new Promise(resolve => setTimeout(resolve, 150));
        
      } catch (error) {
        const errMsg = `Failed to update ${sector.name}: ${error}`;
        console.error(`[Updater] ${errMsg}`);
        errors.push(errMsg);
      }
    }
    
    console.log(`[Updater] Updated ${sectorsUpdated} sectors, ${recordsInserted} records`);
    
    // 3. 计算排名
    if (recordsInserted > 0) {
      rankingsUpdated = await calculateAndStoreRankings();
    }
    
    const duration = Date.now() - startTime;
    console.log(`[Updater] Completed in ${duration}ms`);
    
    return {
      success: true,
      message: `Updated ${sectorsUpdated} sectors, ${recordsInserted} records, ${rankingsUpdated} rankings`,
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
