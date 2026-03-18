#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
重新获取失败的6个行业数据
处理NaN值，将NaN自动置0
"""
import sys
import os
from pathlib import Path

# 添加项目路径到sys.path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root / "server"))

import akshare as ak
import pandas as pd
import numpy as np
from datetime import datetime
import time

# 导入Supabase客户端
from src.storage.database.supabase_client import get_supabase_client


# 失败的6个行业
FAILED_INDUSTRIES = [
    {'name': '养殖业', 'code': '881102'},
    {'name': '工程机械', 'code': '881268'},
    {'name': '风电设备', 'code': '881280'},
    {'name': '游戏', 'code': '881275'},
    {'name': '文化传媒', 'code': '881164'},
    {'name': '多元金融', 'code': '881283'},
]


def clean_nan_value(value):
    """
    清理NaN值，将NaN转换为0
    """
    if pd.isna(value) or (isinstance(value, float) and np.isnan(value)):
        return 0
    return value


def fetch_and_store_industry_data(client, start_date="20240101"):
    """
    重新获取并存储失败行业的历史数据
    
    Args:
        client: Supabase客户端
        start_date: 开始日期，格式：YYYYMMDD
    """
    print("=" * 60)
    print("重新获取失败行业的历史数据")
    print("=" * 60)
    
    end_date = datetime.now().strftime("%Y%m%d")
    print(f"时间范围: {start_date} 至 {end_date}")
    print(f"需要获取 {len(FAILED_INDUSTRIES)} 个行业的数据\n")
    
    success_count = 0
    fail_count = 0
    total_records = 0
    
    for industry in FAILED_INDUSTRIES:
        industry_name = industry['name']
        industry_code = industry['code']
        
        print(f"\n{'='*60}")
        print(f"正在获取: {industry_name} (代码: {industry_code})")
        print('='*60)
        
        try:
            # 获取该行业的历史数据
            industry_data = ak.stock_board_industry_index_ths(
                symbol=industry_name,
                start_date=start_date,
                end_date=end_date
            )
            
            if industry_data is None or len(industry_data) == 0:
                print(f"✗ {industry_name} 没有数据")
                fail_count += 1
                continue
            
            # 显示原始数据信息
            print(f"获取到 {len(industry_data)} 条数据")
            
            # 检查NaN值
            nan_count = industry_data.isna().sum().sum()
            if nan_count > 0:
                print(f"发现 {nan_count} 个NaN值，将自动置0")
            
            # 准备数据，处理NaN值
            data_records = []
            for _, row in industry_data.iterrows():
                # 将日期转换为字符串格式
                trade_date = row['日期']
                if isinstance(trade_date, (pd.Timestamp, datetime)):
                    trade_date = trade_date.strftime('%Y-%m-%d')
                elif not isinstance(trade_date, str):
                    trade_date = str(trade_date)
                
                # 处理所有数值字段，NaN置0
                data_records.append({
                    'sector_code': industry_code,
                    'trade_date': trade_date,
                    'open_price': clean_nan_value(float(row['开盘价'])),
                    'high_price': clean_nan_value(float(row['最高价'])),
                    'low_price': clean_nan_value(float(row['最低价'])),
                    'close_price': clean_nan_value(float(row['收盘价'])),
                    'volume': clean_nan_value(int(row['成交量'])),
                    'amount': clean_nan_value(float(row['成交额']))
                })
            
            # 批量插入数据
            if data_records:
                response = client.table('industry_daily_data').insert(data_records).execute()
                total_records += len(data_records)
                success_count += 1
                print(f"✓ 成功存储 {len(data_records)} 条数据")
            else:
                print(f"✗ 没有有效数据可存储")
                fail_count += 1
            
            # 添加延迟，避免请求过快
            time.sleep(1)
            
        except Exception as e:
            print(f"✗ {industry_name} 数据获取失败: {e}")
            import traceback
            traceback.print_exc()
            fail_count += 1
            continue
    
    print("\n" + "=" * 60)
    print("数据重新获取完成")
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
    print("重新获取失败行业数据工具")
    print("=" * 60)
    print(f"目标行业: {', '.join([i['name'] for i in FAILED_INDUSTRIES])}")
    
    try:
        # 初始化Supabase客户端
        client = get_supabase_client()
        print("✓ Supabase客户端初始化成功")
        
        # 获取并存储行业历史数据
        success, fail, total = fetch_and_store_industry_data(
            client, 
            start_date="20240101"
        )
        
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
