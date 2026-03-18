#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
获取同花顺行业数据并存储到数据库
从2024年1月1日开始至今的历史数据
"""
import sys
import os
from pathlib import Path

# 添加项目路径到sys.path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root / "server"))

import akshare as ak
import pandas as pd
from datetime import datetime
import time
from tqdm import tqdm

# 导入Supabase客户端
from src.storage.database.supabase_client import get_supabase_client


def fetch_and_store_industry_sectors(client):
    """
    获取并存储行业板块列表
    """
    print("=" * 60)
    print("步骤1: 获取行业板块列表")
    print("=" * 60)
    
    try:
        # 获取行业板块列表
        industry_list = ak.stock_board_industry_name_ths()
        print(f"\n获取到 {len(industry_list)} 个行业板块")
        
        # 准备数据
        sectors_data = []
        for _, row in industry_list.iterrows():
            sectors_data.append({
                'name': row['name'],
                'code': str(row['code'])
            })
        
        # 存储到数据库（批量插入）
        # 先删除已有数据
        client.table('industry_sectors').delete().neq('id', 0).execute()
        
        # 批量插入新数据
        response = client.table('industry_sectors').insert(sectors_data).execute()
        print(f"✓ 成功存储 {len(sectors_data)} 个行业板块到数据库")
        
        return sectors_data
        
    except Exception as e:
        print(f"✗ 获取行业板块列表失败: {e}")
        raise


def fetch_and_store_industry_data(client, sectors, start_date="20240101"):
    """
    获取并存储行业历史数据
    
    Args:
        client: Supabase客户端
        sectors: 行业板块列表
        start_date: 开始日期，格式：YYYYMMDD
    """
    print("\n" + "=" * 60)
    print("步骤2: 获取行业历史数据")
    print("=" * 60)
    
    end_date = datetime.now().strftime("%Y%m%d")
    print(f"时间范围: {start_date} 至 {end_date}")
    print(f"需要获取 {len(sectors)} 个行业的数据\n")
    
    success_count = 0
    fail_count = 0
    total_records = 0
    
    # 使用进度条
    for sector in tqdm(sectors, desc="获取行业数据"):
        sector_name = sector['name']
        sector_code = sector['code']
        
        try:
            # 获取该行业的历史数据
            industry_data = ak.stock_board_industry_index_ths(
                symbol=sector_name,
                start_date=start_date,
                end_date=end_date
            )
            
            if industry_data is None or len(industry_data) == 0:
                print(f"\n  警告: {sector_name} 没有数据")
                fail_count += 1
                continue
            
            # 准备数据
            data_records = []
            for _, row in industry_data.iterrows():
                # 将日期转换为字符串格式
                trade_date = row['日期']
                if isinstance(trade_date, (pd.Timestamp, datetime)):
                    trade_date = trade_date.strftime('%Y-%m-%d')
                elif not isinstance(trade_date, str):
                    trade_date = str(trade_date)
                
                data_records.append({
                    'sector_code': sector_code,
                    'trade_date': trade_date,
                    'open_price': float(row['开盘价']),
                    'high_price': float(row['最高价']),
                    'low_price': float(row['最低价']),
                    'close_price': float(row['收盘价']),
                    'volume': int(row['成交量']),
                    'amount': float(row['成交额'])
                })
            
            # 批量插入数据
            if data_records:
                response = client.table('industry_daily_data').insert(data_records).execute()
                total_records += len(data_records)
                success_count += 1
            
            # 添加延迟，避免请求过快
            time.sleep(0.5)
            
        except Exception as e:
            print(f"\n  ✗ {sector_name} 数据获取失败: {e}")
            fail_count += 1
            continue
    
    print("\n" + "=" * 60)
    print("数据获取完成")
    print("=" * 60)
    print(f"✓ 成功: {success_count} 个行业")
    print(f"✗ 失败: {fail_count} 个行业")
    print(f"✓ 总记录数: {total_records} 条")
    
    return success_count, fail_count, total_records


def main():
    """
    主函数
    """
    print("\n" + "=" * 60)
    print("同花顺行业数据采集工具")
    print("=" * 60)
    
    try:
        # 初始化Supabase客户端
        client = get_supabase_client()
        print("✓ Supabase客户端初始化成功")
        
        # 获取并存储行业板块
        sectors = fetch_and_store_industry_sectors(client)
        
        # 获取并存储行业历史数据
        success, fail, total = fetch_and_store_industry_data(
            client, 
            sectors, 
            start_date="20240101"
        )
        
        print("\n" + "=" * 60)
        print("数据采集完成！")
        print("=" * 60)
        
    except Exception as e:
        print(f"\n✗ 程序执行失败: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
