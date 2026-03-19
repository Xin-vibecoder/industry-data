#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
获取A股ETF基金数据
从2024年1月1日开始获取所有ETF的历史行情数据
优化版：增加请求间隔、重试机制、随机延迟等
"""
import sys
import os
import random
import time
from pathlib import Path
from datetime import datetime, timedelta

project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root / "server"))

import akshare as ak
import pandas as pd
import numpy as np
from src.storage.database.supabase_client import get_supabase_client

LOG_FILE = "/app/work/logs/bypass/etf_update.log"

# 请求配置
BASE_DELAY = 0.5          # 基础延迟（秒）
MAX_DELAY = 3.0           # 最大延迟（秒）
RETRY_TIMES = 3           # 重试次数
RETRY_DELAY = 5.0         # 重试延迟（秒）
BATCH_SIZE = 50           # 每批处理后休息
BATCH_BREAK = 10.0        # 批次间休息时间（秒）


def log(message):
    """记录日志"""
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    log_message = f"[{timestamp}] {message}"
    print(log_message)
    os.makedirs(os.path.dirname(LOG_FILE), exist_ok=True)
    with open(LOG_FILE, "a", encoding="utf-8") as f:
        f.write(log_message + "\n")


def clean_nan(val):
    """处理NaN值"""
    if pd.isna(val) or (isinstance(val, float) and np.isnan(val)):
        return None
    return val


def random_delay(base=BASE_DELAY, max_delay=MAX_DELAY):
    """随机延迟"""
    delay = base + random.random() * (max_delay - base)
    time.sleep(delay)


def fetch_with_retry(func, *args, **kwargs):
    """带重试的请求"""
    last_error = None
    for attempt in range(RETRY_TIMES):
        try:
            result = func(*args, **kwargs)
            return result, None
        except Exception as e:
            last_error = e
            if attempt < RETRY_TIMES - 1:
                # 指数退避
                wait_time = RETRY_DELAY * (2 ** attempt) + random.random() * 2
                log(f"    重试 {attempt + 1}/{RETRY_TIMES}, 等待 {wait_time:.1f}s...")
                time.sleep(wait_time)
    return None, last_error


def fetch_etf_list(client):
    """
    获取ETF列表
    """
    log("=" * 60)
    log("步骤1: 获取ETF列表")
    log("=" * 60)
    
    try:
        # 使用新浪接口获取ETF列表（更稳定）
        df, error = fetch_with_retry(ak.fund_etf_category_sina, symbol="ETF基金")
        
        if error or df is None or len(df) == 0:
            log(f"未获取到ETF数据: {error}")
            return []
        
        log(f"获取到 {len(df)} 只ETF")
        random_delay(1.0, 2.0)
        
        # 处理数据
        etf_list = []
        for _, row in df.iterrows():
            code = str(row.get('代码', ''))
            name = str(row.get('名称', ''))
            
            # 判断交易所
            if code.startswith('5') or code.startswith('58'):
                exchange = 'SH'
            elif code.startswith('1') or code.startswith('15') or code.startswith('16'):
                exchange = 'SZ'
            else:
                exchange = 'UNKNOWN'
            
            # 判断ETF类型
            if '货币' in name or '理财' in name:
                etf_type = '货币型'
            elif '债' in name:
                etf_type = '债券型'
            elif '黄金' in name or '白银' in name or '商品' in name:
                etf_type = '商品型'
            elif '跨境' in name or '纳指' in name or '标普' in name or '恒生' in name or '港股' in name or '中概' in name:
                etf_type = '跨境型'
            else:
                etf_type = '股票型'
            
            etf_list.append({
                'code': code,
                'name': name,
                'type': etf_type,
                'exchange': exchange
            })
        
        # 存储到数据库
        if etf_list:
            client.table('etf_info').delete().neq('id', 0).execute()
            
            batch_size = 500
            for i in range(0, len(etf_list), batch_size):
                batch = etf_list[i:i+batch_size]
                client.table('etf_info').insert(batch).execute()
                time.sleep(0.2)
            
            log(f"✓ 成功存储 {len(etf_list)} 只ETF信息")
        
        return etf_list
        
    except Exception as e:
        log(f"获取ETF列表失败: {e}")
        import traceback
        traceback.print_exc()
        return []


def fetch_etf_history(client, etf_list, start_date='20240101'):
    """
    获取ETF历史行情数据（优化版）
    """
    log("=" * 60)
    log(f"步骤2: 获取ETF历史行情数据（从{start_date}开始）")
    log(f"配置: 基础延迟={BASE_DELAY}s, 重试={RETRY_TIMES}次, 批次大小={BATCH_SIZE}")
    log("=" * 60)
    
    end_date = datetime.now().strftime('%Y%m%d')
    total_count = len(etf_list)
    success_count = 0
    fail_count = 0
    total_records = 0
    failed_etfs = []  # 记录失败的ETF
    
    for idx, etf in enumerate(etf_list):
        code = etf['code'].replace('sz', '').replace('sh', '')
        name = etf['name']
        
        # 批次休息
        if idx > 0 and idx % BATCH_SIZE == 0:
            log(f"  --- 已处理 {idx} 只，休息 {BATCH_BREAK}s ---")
            time.sleep(BATCH_BREAK)
        
        try:
            # 使用重试机制获取数据
            df, error = fetch_with_retry(
                ak.fund_etf_hist_em,
                symbol=code,
                period='daily',
                start_date=start_date,
                end_date=end_date,
                adjust='qfq'
            )
            
            if error:
                fail_count += 1
                failed_etfs.append({'code': code, 'name': name, 'error': str(error)[:100]})
                log(f"  [{idx+1}/{total_count}] {code} {name}: 失败 - {str(error)[:50]}")
                random_delay(1.0, 2.0)  # 失败后多等待一会
                continue
            
            if df is None or len(df) == 0:
                log(f"  [{idx+1}/{total_count}] {code} {name}: 无历史数据")
                random_delay()
                continue
            
            # 准备数据记录
            data_records = []
            for _, row in df.iterrows():
                trade_date = row.get('日期', row.get('date', ''))
                if isinstance(trade_date, (pd.Timestamp, datetime)):
                    trade_date = trade_date.strftime('%Y-%m-%d')
                elif not isinstance(trade_date, str):
                    trade_date = str(trade_date)
                
                if '-' not in trade_date:
                    trade_date = f"{trade_date[:4]}-{trade_date[4:6]}-{trade_date[6:]}"
                
                data_records.append({
                    'etf_code': code,
                    'trade_date': trade_date,
                    'open_price': clean_nan(row.get('开盘', row.get('open'))),
                    'high_price': clean_nan(row.get('最高', row.get('high'))),
                    'low_price': clean_nan(row.get('最低', row.get('low'))),
                    'close_price': clean_nan(row.get('收盘', row.get('close'))),
                    'volume': int(clean_nan(row.get('成交量', row.get('volume'))) or 0),
                    'amount': clean_nan(row.get('成交额', row.get('amount'))),
                    'change_pct': clean_nan(row.get('涨跌幅', row.get('change'))),
                    'turnover_rate': clean_nan(row.get('换手率', row.get('turnover')))
                })
            
            if data_records:
                # 删除已有数据
                client.table('etf_daily_data')\
                    .delete()\
                    .eq('etf_code', code)\
                    .execute()
                
                # 分批插入
                batch_insert_size = 500
                for i in range(0, len(data_records), batch_insert_size):
                    batch = data_records[i:i+batch_insert_size]
                    client.table('etf_daily_data').insert(batch).execute()
                    time.sleep(0.1)
                
                total_records += len(data_records)
                success_count += 1
                log(f"  [{idx+1}/{total_count}] {code} {name}: {len(data_records)} 条 ✓")
            
            # 随机延迟
            random_delay()
            
        except Exception as e:
            fail_count += 1
            failed_etfs.append({'code': code, 'name': name, 'error': str(e)[:100]})
            log(f"  [{idx+1}/{total_count}] {code} {name}: 异常 - {str(e)[:50]}")
            random_delay(1.0, 2.0)
            continue
    
    log("=" * 60)
    log(f"历史数据获取完成: 成功 {success_count}, 失败 {fail_count}, 总记录 {total_records}")
    log("=" * 60)
    
    # 记录失败的ETF
    if failed_etfs:
        log(f"\n失败的ETF列表 ({len(failed_etfs)}只):")
        for etf in failed_etfs[:20]:  # 只显示前20个
            log(f"  {etf['code']} {etf['name']}: {etf['error']}")
        if len(failed_etfs) > 20:
            log(f"  ... 还有 {len(failed_etfs) - 20} 只")
    
    return total_records, failed_etfs


def retry_failed_etfs(client, failed_etfs, start_date='20240101'):
    """
    重试获取失败的ETF数据
    """
    if not failed_etfs:
        return 0
    
    log("=" * 60)
    log(f"步骤3: 重试失败的ETF ({len(failed_etfs)}只)")
    log("=" * 60)
    
    end_date = datetime.now().strftime('%Y%m%d')
    total_records = 0
    still_failed = []
    
    for idx, etf in enumerate(failed_etfs):
        code = etf['code']
        name = etf['name']
        
        # 批次休息
        if idx > 0 and idx % 20 == 0:
            log(f"  --- 已重试 {idx} 只，休息 15s ---")
            time.sleep(15)
        
        # 更长的延迟
        time.sleep(2.0 + random.random() * 2.0)
        
        try:
            df, error = fetch_with_retry(
                ak.fund_etf_hist_em,
                symbol=code,
                period='daily',
                start_date=start_date,
                end_date=end_date,
                adjust='qfq'
            )
            
            if error or df is None or len(df) == 0:
                still_failed.append(etf)
                log(f"  [{idx+1}/{len(failed_etfs)}] {code} {name}: 仍然失败")
                continue
            
            data_records = []
            for _, row in df.iterrows():
                trade_date = row.get('日期', row.get('date', ''))
                if isinstance(trade_date, (pd.Timestamp, datetime)):
                    trade_date = trade_date.strftime('%Y-%m-%d')
                elif not isinstance(trade_date, str):
                    trade_date = str(trade_date)
                
                if '-' not in trade_date:
                    trade_date = f"{trade_date[:4]}-{trade_date[4:6]}-{trade_date[6:]}"
                
                data_records.append({
                    'etf_code': code,
                    'trade_date': trade_date,
                    'open_price': clean_nan(row.get('开盘', row.get('open'))),
                    'high_price': clean_nan(row.get('最高', row.get('high'))),
                    'low_price': clean_nan(row.get('最低', row.get('low'))),
                    'close_price': clean_nan(row.get('收盘', row.get('close'))),
                    'volume': int(clean_nan(row.get('成交量', row.get('volume'))) or 0),
                    'amount': clean_nan(row.get('成交额', row.get('amount'))),
                    'change_pct': clean_nan(row.get('涨跌幅', row.get('change'))),
                    'turnover_rate': clean_nan(row.get('换手率', row.get('turnover')))
                })
            
            if data_records:
                client.table('etf_daily_data').delete().eq('etf_code', code).execute()
                
                for i in range(0, len(data_records), 500):
                    batch = data_records[i:i+500]
                    client.table('etf_daily_data').insert(batch).execute()
                    time.sleep(0.1)
                
                total_records += len(data_records)
                log(f"  [{idx+1}/{len(failed_etfs)}] {code} {name}: {len(data_records)} 条 ✓")
        
        except Exception as e:
            still_failed.append(etf)
            log(f"  [{idx+1}/{len(failed_etfs)}] {code} {name}: 异常 - {str(e)[:50]}")
    
    log(f"\n重试完成: 成功获取 {len(failed_etfs) - len(still_failed)} 只, 仍有 {len(still_failed)} 只失败")
    
    return total_records


def main():
    """主函数"""
    log("\n" + "=" * 60)
    log("ETF数据获取任务启动（优化版）")
    log(f"配置: 基础延迟={BASE_DELAY}s, 最大延迟={MAX_DELAY}s, 重试次数={RETRY_TIMES}")
    log("=" * 60)
    
    try:
        client = get_supabase_client()
        log("✓ Supabase客户端初始化成功")
        
        # 获取ETF列表
        etf_list = fetch_etf_list(client)
        
        if not etf_list:
            log("未获取到ETF列表，任务结束")
            return 1
        
        # 获取历史行情数据
        total_records, failed_etfs = fetch_etf_history(client, etf_list, start_date='20240101')
        
        # 重试失败的ETF
        if failed_etfs:
            log(f"\n等待30秒后重试失败的ETF...")
            time.sleep(30)
            retry_records = retry_failed_etfs(client, failed_etfs, start_date='20240101')
            total_records += retry_records
        
        # 最终统计
        result = client.table('etf_daily_data').select('id', count='exact').execute()
        final_count = result.count
        
        log("\n" + "=" * 60)
        log("✓ ETF数据获取任务完成")
        log(f"数据库中共有 {final_count} 条历史记录")
        log("=" * 60)
        
        return 0
        
    except Exception as e:
        log(f"任务执行失败: {e}")
        import traceback
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    sys.exit(main())
