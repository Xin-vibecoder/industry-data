#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
自动更新同花顺行业数据
每天晚上7点执行，失败则8点重试
"""
import sys
import os
from pathlib import Path
from datetime import datetime, timedelta
import time
import json

# 添加项目路径到sys.path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root / "server"))

import akshare as ak
import pandas as pd
import numpy as np

# 导入Supabase客户端
from src.storage.database.supabase_client import get_supabase_client

# 日志文件路径
LOG_FILE = "/app/work/logs/bypass/auto_update.log"


def log(message):
    """记录日志"""
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    log_message = f"[{timestamp}] {message}"
    print(log_message)
    
    # 写入日志文件
    os.makedirs(os.path.dirname(LOG_FILE), exist_ok=True)
    with open(LOG_FILE, "a", encoding="utf-8") as f:
        f.write(log_message + "\n")


def fetch_recent_industry_data(client, days=3):
    """
    获取最近N天的行业数据
    
    Args:
        client: Supabase客户端
        days: 获取最近几天的数据
    """
    log("=" * 60)
    log(f"开始获取最近 {days} 天的行业数据")
    log("=" * 60)
    
    try:
        # 获取所有行业板块
        log("步骤1: 获取行业板块列表...")
        industry_list = ak.stock_board_industry_name_ths()
        log(f"✓ 获取到 {len(industry_list)} 个行业板块")
        
        # 计算日期范围
        end_date = datetime.now().strftime("%Y%m%d")
        start_date = (datetime.now() - timedelta(days=days*2)).strftime("%Y%m%d")  # 多获取几天以确保覆盖
        log(f"日期范围: {start_date} 至 {end_date}")
        
        # 获取每个行业的数据
        success_count = 0
        fail_count = 0
        total_records = 0
        
        for _, industry_row in industry_list.iterrows():
            industry_name = industry_row['name']
            industry_code = str(industry_row['code'])
            
            try:
                # 获取该行业的数据
                industry_data = ak.stock_board_industry_index_ths(
                    symbol=industry_name,
                    start_date=start_date,
                    end_date=end_date
                )
                
                if industry_data is None or len(industry_data) == 0:
                    continue
                
                # 筛选最近N天的数据
                recent_dates = []
                for i in range(days):
                    date = (datetime.now() - timedelta(days=i)).strftime("%Y-%m-%d")
                    recent_dates.append(date)
                
                recent_data = industry_data[industry_data['日期'].astype(str).isin(recent_dates)]
                
                if len(recent_data) == 0:
                    continue
                
                # 准备数据
                data_records = []
                for _, row in recent_data.iterrows():
                    # 处理日期格式
                    trade_date = row['日期']
                    if isinstance(trade_date, (pd.Timestamp, datetime)):
                        trade_date = trade_date.strftime('%Y-%m-%d')
                    elif not isinstance(trade_date, str):
                        trade_date = str(trade_date)
                    
                    # 处理NaN值
                    def clean_nan(val):
                        if pd.isna(val) or (isinstance(val, float) and np.isnan(val)):
                            return 0
                        return val
                    
                    data_records.append({
                        'sector_code': industry_code,
                        'trade_date': trade_date,
                        'open_price': float(clean_nan(row['开盘价'])),
                        'high_price': float(clean_nan(row['最高价'])),
                        'low_price': float(clean_nan(row['最低价'])),
                        'close_price': float(clean_nan(row['收盘价'])),
                        'volume': int(clean_nan(row['成交量'])),
                        'amount': float(clean_nan(row['成交额']))
                    })
                
                if data_records:
                    # 先删除已有数据（避免重复）
                    for record in data_records:
                        client.table('industry_daily_data')\
                            .delete()\
                            .eq('sector_code', record['sector_code'])\
                            .eq('trade_date', record['trade_date'])\
                            .execute()
                    
                    # 插入新数据
                    client.table('industry_daily_data').insert(data_records).execute()
                    total_records += len(data_records)
                    success_count += 1
                
                # 延迟避免请求过快
                time.sleep(0.3)
                
            except Exception as e:
                log(f"  ✗ {industry_name} 获取失败: {e}")
                fail_count += 1
                continue
        
        log(f"✓ 数据获取完成: 成功 {success_count}, 失败 {fail_count}, 总记录 {total_records}")
        return True, total_records
        
    except Exception as e:
        log(f"✗ 数据获取失败: {e}")
        import traceback
        traceback.print_exc()
        return False, 0


def incremental_update_rankings(client, days=5):
    """
    增量更新排名数据
    
    Args:
        client: Supabase客户端
        days: 更新最近几天的排名
    """
    log("=" * 60)
    log(f"开始增量更新排名数据（最近 {days} 天）")
    log("=" * 60)
    
    try:
        # 导入计算排名的函数
        from calculate_rankings import calculate_and_store_rankings
        
        # 执行增量更新
        calculate_and_store_rankings(client, incremental_days=days)
        
        log("✓ 排名数据更新完成")
        return True
        
    except Exception as e:
        log(f"✗ 排名数据更新失败: {e}")
        import traceback
        traceback.print_exc()
        return False


def main():
    """
    主函数
    """
    log("\n" + "=" * 60)
    log("自动更新任务启动")
    log("=" * 60)
    
    try:
        # 初始化Supabase客户端
        client = get_supabase_client()
        log("✓ Supabase客户端初始化成功")
        
        # 获取最近3天的行业数据
        success, total_records = fetch_recent_industry_data(client, days=3)
        
        if success and total_records > 0:
            # 数据获取成功，执行增量更新
            log("\n数据获取成功，开始增量更新排名...")
            update_success = incremental_update_rankings(client, days=5)
            
            if update_success:
                log("\n" + "=" * 60)
                log("✓ 自动更新任务完成")
                log("=" * 60)
                return 0
            else:
                log("\n✗ 排名更新失败")
                return 1
        else:
            log("\n✗ 数据获取失败或无新数据")
            return 1
        
    except Exception as e:
        log(f"\n✗ 任务执行失败: {e}")
        import traceback
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)
