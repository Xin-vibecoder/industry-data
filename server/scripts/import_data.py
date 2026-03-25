#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
将导出的 JSON 数据导入到 Supabase 数据库
用于在新环境中初始化数据
"""
import json
import os
import sys
from pathlib import Path

# 添加项目路径
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from server.src.storage.database.supabase_client import get_supabase_client


def import_sectors(client, file_path):
    """导入行业板块数据"""
    print(f"导入行业板块数据: {file_path}")
    with open(file_path, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    if not data:
        print("  无数据")
        return 0
    
    # 批量插入，每批 100 条
    batch_size = 100
    total = 0
    for i in range(0, len(data), batch_size):
        batch = data[i:i+batch_size]
        try:
            client.table('industry_sectors').insert(batch).execute()
            total += len(batch)
            print(f"  已导入 {total}/{len(data)} 条")
        except Exception as e:
            print(f"  批次 {i//batch_size} 导入失败: {e}")
    
    return total


def import_daily_data(client, file_path):
    """导入每日数据"""
    print(f"导入每日数据: {file_path}")
    with open(file_path, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    if not data:
        print("  无数据")
        return 0
    
    # 批量插入，每批 500 条
    batch_size = 500
    total = 0
    for i in range(0, len(data), batch_size):
        batch = data[i:i+batch_size]
        try:
            client.table('industry_daily_data').insert(batch).execute()
            total += len(batch)
            print(f"  已导入 {total}/{len(data)} 条")
        except Exception as e:
            print(f"  批次 {i//batch_size} 导入失败: {e}")
    
    return total


def import_rankings(client, file_path):
    """导入排名数据"""
    print(f"导入排名数据: {file_path}")
    with open(file_path, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    if not data:
        print("  无数据")
        return 0
    
    # 批量插入，每批 500 条
    batch_size = 500
    total = 0
    for i in range(0, len(data), batch_size):
        batch = data[i:i+batch_size]
        try:
            client.table('industry_rankings').insert(batch).execute()
            total += len(batch)
            print(f"  已导入 {total}/{len(data)} 条")
        except Exception as e:
            print(f"  批次 {i//batch_size} 导入失败: {e}")
    
    return total


def main():
    print("=" * 60)
    print("Supabase 数据导入工具")
    print("=" * 60)
    
    # 初始化客户端
    print("\n初始化 Supabase 客户端...")
    client = get_supabase_client()
    print("✓ 客户端初始化成功")
    
    # 数据文件路径
    data_dir = Path(__file__).parent
    
    # 导入行业板块
    sectors_file = data_dir / 'industry_sectors.json'
    if sectors_file.exists():
        count = import_sectors(client, sectors_file)
        print(f"✓ 行业板块导入完成: {count} 条\n")
    else:
        print(f"✗ 文件不存在: {sectors_file}\n")
    
    # 导入每日数据
    daily_file = data_dir / 'industry_daily_data.json'
    if daily_file.exists():
        count = import_daily_data(client, daily_file)
        print(f"✓ 每日数据导入完成: {count} 条\n")
    else:
        print(f"✗ 文件不存在: {daily_file}\n")
    
    # 导入排名数据
    rankings_file = data_dir / 'industry_rankings.json'
    if rankings_file.exists():
        count = import_rankings(client, rankings_file)
        print(f"✓ 排名数据导入完成: {count} 条\n")
    else:
        print(f"✗ 文件不存在: {rankings_file}\n")
    
    print("=" * 60)
    print("数据导入完成")
    print("=" * 60)


if __name__ == "__main__":
    main()
