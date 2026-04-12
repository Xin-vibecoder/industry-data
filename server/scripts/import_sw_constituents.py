#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
将申万行业成分股数据导入到 Supabase 数据库
"""
import json
import sys
from pathlib import Path

# 添加项目路径
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from server.src.storage.database.supabase_client import get_supabase_client


def load_json(file_path):
    """加载 JSON 文件"""
    with open(file_path, 'r', encoding='utf-8') as f:
        return json.load(f)


def transform_data(data):
    """
    转换数据格式
    列名映射：股票代码 -> stock_code, 股票简称 -> stock_name, etc.
    """
    records = []
    for item in data:
        record = {
            'stock_code': item.get('股票代码', ''),
            'stock_name': item.get('股票简称', ''),
            'industry_level1': item.get('申万1级', ''),
            'industry_level2': item.get('申万2级', ''),
            'industry_level3': item.get('申万3级', ''),
            'inclusion_date': item.get('纳入时间', ''),
            'price': float(item['价格']) if item.get('价格') else None,
            'pe_ratio': float(item['市盈率']) if item.get('市盈率') else None,
            'pe_ttm': float(item['市盈率ttm']) if item.get('市盈率ttm') else None,
            'pb_ratio': float(item['市净率']) if item.get('市净率') else None,
            'dividend_yield': float(item['股息率']) if item.get('股息率') else None,
            'market_cap': float(item['市值']) if item.get('市值') else None,
        }
        records.append(record)
    return records


def import_to_supabase(data):
    """
    导入数据到 Supabase
    """
    client = get_supabase_client()
    
    # 先清空旧数据
    print("清空旧数据...")
    try:
        client.table('sw_industry_constituents').delete().neq('id', 0).execute()
    except Exception as e:
        print(f"  清空失败（可能表不存在）: {e}")
        print("请先在 Supabase 中执行 create_constituents_table.sql 创建表")
        return 0
    
    # 批量插入
    batch_size = 500
    total = 0
    
    print(f"开始导入 {len(data)} 条数据...")
    
    for i in range(0, len(data), batch_size):
        batch = data[i:i+batch_size]
        try:
            client.table('sw_industry_constituents').insert(batch).execute()
            total += len(batch)
            print(f"  已导入 {total}/{len(data)} 条")
        except Exception as e:
            print(f"  批次 {i//batch_size} 导入失败: {e}")
    
    return total


def main():
    print("=" * 60)
    print("申万行业成分股数据导入工具")
    print("=" * 60)
    
    # 数据文件路径
    script_dir = Path(__file__).parent
    json_file = script_dir / 'sw_industry_constituents.json'
    
    if not json_file.exists():
        print(f"\n错误: 文件不存在 - {json_file}")
        print("请先运行 fetch_sw_constituents.py 获取数据")
        return
    
    # 加载数据
    print(f"\n加载数据: {json_file}")
    data = load_json(json_file)
    print(f"加载了 {len(data)} 条记录")
    
    # 转换数据
    print("\n转换数据格式...")
    records = transform_data(data)
    print(f"转换完成: {len(records)} 条")
    
    # 导入到数据库
    print("\n初始化 Supabase 客户端...")
    total = import_to_supabase(records)
    
    if total > 0:
        print("\n" + "=" * 60)
        print(f"✓ 导入完成! 共导入 {total} 条数据")
        print("=" * 60)
    else:
        print("\n导入失败，请检查错误信息")


if __name__ == "__main__":
    main()
