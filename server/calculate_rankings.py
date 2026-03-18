#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
计算并存储行业排名数据到数据库
支持全量计算和增量更新
"""
import sys
import os
from pathlib import Path

# 添加项目路径到sys.path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root / "server"))

import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from typing import List, Dict, Optional

# 导入Supabase客户端
from src.storage.database.supabase_client import get_supabase_client


def calculate_change(current_close: float, previous_close: Optional[float]) -> Optional[float]:
    """
    计算涨跌幅
    """
    if previous_close is None or previous_close == 0:
        return None
    return ((current_close - previous_close) / previous_close) * 100


def calculate_and_store_rankings(client, incremental_days: int = 0):
    """
    计算并存储排名数据
    
    Args:
        client: Supabase客户端
        incremental_days: 增量更新天数，0表示全量更新
    """
    print("=" * 60)
    print("计算行业排名数据")
    print("=" * 60)
    
    if incremental_days > 0:
        print(f"模式: 增量更新（最近 {incremental_days} 天）")
    else:
        print("模式: 全量更新")
    
    # 1. 获取所有行业数据
    print("\n步骤1: 获取行业数据...")
    response = client.table('industry_daily_data').select('*').order('trade_date', desc=True).execute()
    all_data = response.data
    
    if not all_data:
        print("✗ 没有数据")
        return
    
    print(f"✓ 获取到 {len(all_data)} 条数据")
    
    # 2. 转换为DataFrame
    df = pd.DataFrame(all_data)
    
    # 3. 按行业分组
    sector_groups = df.groupby('sector_code')
    
    # 4. 计算每个行业的涨跌幅
    print("\n步骤2: 计算涨跌幅...")
    
    results = []
    for sector_code in df['sector_code'].unique():
        sector_df = df[df['sector_code'] == sector_code].copy()
        # 按日期倒序排列
        sector_df = sector_df.sort_values('trade_date', ascending=False).reset_index(drop=True)
        
        for idx, row in sector_df.iterrows():
            # 每日涨跌幅
            prev_close = sector_df.iloc[idx + 1]['close_price'] if idx < len(sector_df) - 1 else None
            daily_change = calculate_change(row['close_price'], prev_close)
            
            # 五日涨跌
            five_day_close = sector_df.iloc[idx + 5]['close_price'] if idx < len(sector_df) - 5 else None
            five_day_change = calculate_change(row['close_price'], five_day_close)
            
            # 二十日涨跌
            twenty_day_close = sector_df.iloc[idx + 20]['close_price'] if idx < len(sector_df) - 20 else None
            twenty_day_change = calculate_change(row['close_price'], twenty_day_close)
            
            results.append({
                'sector_code': sector_code,
                'trade_date': row['trade_date'],
                'daily_change': daily_change,
                'five_day_change': five_day_change,
                'twenty_day_change': twenty_day_change,
            })
    
    results_df = pd.DataFrame(results)
    print(f"✓ 计算了 {len(results_df)} 条记录的涨跌幅")
    
    # 5. 计算排名
    print("\n步骤3: 计算排名...")
    
    # 获取所有日期
    all_dates = results_df['trade_date'].unique()
    
    # 如果是增量更新，只处理最近的N天
    if incremental_days > 0:
        all_dates = sorted(all_dates, reverse=True)[:incremental_days]
        print(f"✓ 仅处理最近 {incremental_days} 天: {all_dates}")
    
    rankings = []
    for date in all_dates:
        date_data = results_df[results_df['trade_date'] == date]
        
        # 五日排名（涨幅越大，排名越小）
        valid_five_day = date_data[date_data['five_day_change'].notna()].copy()
        valid_five_day['five_day_rank'] = valid_five_day['five_day_change'].rank(ascending=False, method='min')
        
        # 二十日排名
        valid_twenty_day = date_data[date_data['twenty_day_change'].notna()].copy()
        valid_twenty_day['twenty_day_rank'] = valid_twenty_day['twenty_day_change'].rank(ascending=False, method='min')
        
        # 合并排名
        for _, row in date_data.iterrows():
            five_day_rank = valid_five_day.loc[valid_five_day['sector_code'] == row['sector_code'], 'five_day_rank'].values
            five_day_rank = int(five_day_rank[0]) if len(five_day_rank) > 0 and not pd.isna(five_day_rank[0]) else None
            
            twenty_day_rank = valid_twenty_day.loc[valid_twenty_day['sector_code'] == row['sector_code'], 'twenty_day_rank'].values
            twenty_day_rank = int(twenty_day_rank[0]) if len(twenty_day_rank) > 0 and not pd.isna(twenty_day_rank[0]) else None
            
            rankings.append({
                'sector_code': row['sector_code'],
                'trade_date': row['trade_date'],
                'daily_change': row['daily_change'],
                'five_day_change': row['five_day_change'],
                'twenty_day_change': row['twenty_day_change'],
                'five_day_rank': five_day_rank,
                'twenty_day_rank': twenty_day_rank,
            })
    
    rankings_df = pd.DataFrame(rankings)
    print(f"✓ 计算了 {len(rankings_df)} 条记录的排名")
    
    # 6. 存储到数据库
    print("\n步骤4: 存储到数据库...")
    
    # 如果是增量更新，先删除旧数据
    if incremental_days > 0 and len(all_dates) > 0:
        for date in all_dates:
            client.table('industry_rankings').delete().eq('trade_date', date).execute()
        print(f"✓ 删除了 {len(all_dates)} 天的旧数据")
    else:
        # 全量更新，清空表
        client.table('industry_rankings').delete().neq('id', 0).execute()
        print("✓ 清空了所有旧数据")
    
    # 批量插入新数据
    batch_size = 1000
    total_inserted = 0
    
    for i in range(0, len(rankings_df), batch_size):
        batch = rankings_df.iloc[i:i + batch_size].to_dict('records')
        # 处理NaN值和类型转换
        for record in batch:
            for key, value in record.items():
                if pd.isna(value):
                    record[key] = None
                elif key in ['five_day_rank', 'twenty_day_rank']:
                    # 确保排名是整数
                    record[key] = int(value) if value is not None else None
                elif key in ['daily_change', 'five_day_change', 'twenty_day_change']:
                    # 确保浮点数
                    record[key] = float(value) if value is not None else None
        
        response = client.table('industry_rankings').insert(batch).execute()
        total_inserted += len(batch)
        print(f"  进度: {total_inserted}/{len(rankings_df)}")
    
    print(f"\n✓ 成功存储 {total_inserted} 条记录到数据库")
    
    # 7. 显示统计信息
    print("\n" + "=" * 60)
    print("统计信息")
    print("=" * 60)
    print(f"总记录数: {len(rankings_df)}")
    print(f"行业数量: {rankings_df['sector_code'].nunique()}")
    print(f"日期数量: {rankings_df['trade_date'].nunique()}")
    print(f"日期范围: {rankings_df['trade_date'].min()} 至 {rankings_df['trade_date'].max()}")


def main():
    """
    主函数
    """
    import argparse
    
    parser = argparse.ArgumentParser(description='计算并存储行业排名数据')
    parser.add_argument('--incremental', type=int, default=0, 
                       help='增量更新天数，0表示全量更新（默认: 0）')
    
    args = parser.parse_args()
    
    print("\n" + "=" * 60)
    print("行业排名数据计算工具")
    print("=" * 60)
    
    try:
        # 初始化Supabase客户端
        client = get_supabase_client()
        print("✓ Supabase客户端初始化成功")
        
        # 计算并存储排名
        calculate_and_store_rankings(client, incremental_days=args.incremental)
        
        print("\n" + "=" * 60)
        print("任务完成！")
        print("=" * 60)
        
    except Exception as e:
        print(f"\n✗ 程序执行失败: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
