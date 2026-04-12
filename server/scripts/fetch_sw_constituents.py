#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
获取申万行业成分股
可以获取每个行业包含的股票列表及详细信息
"""
import sys
import os
from pathlib import Path
import json
import time
import pandas as pd

# 添加项目路径
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

import akshare as ak


def get_sw_industry_list():
    """
    获取申万行业列表
    """
    print("获取申万行业列表...")
    
    try:
        # 申万一级行业列表
        industries = [
            ('农林牧渔', '801010.SI'),
            ('采掘', '801020.SI'),
            ('化工', '801030.SI'),
            ('钢铁', '801040.SI'),
            ('有色金属', '801050.SI'),
            ('电子', '801080.SI'),
            ('汽车', '801110.SI'),
            ('家用电器', '801110.SI'),
            ('食品饮料', '801120.SI'),
            ('纺织服装', '801130.SI'),
            ('轻工制造', '801140.SI'),
            ('医药生物', '801150.SI'),
            ('公用事业', '801160.SI'),
            ('交通运输', '801170.SI'),
            ('房地产', '801180.SI'),
            ('商业贸易', '801200.SI'),
            ('休闲服务', '801210.SI'),
            ('银行', '801780.SI'),
            ('非银金融', '801790.SI'),
            ('建筑材料', '801710.SI'),
            ('建筑装饰', '801720.SI'),
            ('电气设备', '801730.SI'),
            ('国防军工', '801740.SI'),
            ('计算机', '801750.SI'),
            ('传媒', '801760.SI'),
            ('通信', '801770.SI'),
            ('机械设备', '801780.SI'),
        ]
        
        print(f"获取到 {len(industries)} 个申万一级行业")
        return industries
        
    except Exception as e:
        print(f"获取行业列表失败: {e}")
        return []


def get_sw_industry_constituents(symbol, industry_name):
    """
    获取指定申万行业的成分股
    
    Args:
        symbol: 申万行业代码 (如 '801120.SI')
        industry_name: 行业名称
    
    Returns:
        DataFrame: 成分股列表
    """
    try:
        df = ak.sw_index_third_cons(symbol=symbol)
        df['申万一级'] = industry_name
        return df
    except Exception as e:
        print(f"  获取 {industry_name} 成分股失败: {e}")
        return None


def fetch_all_constituents():
    """
    获取所有申万行业成分股
    """
    print("=" * 60)
    print("申万行业成分股获取工具")
    print("=" * 60)
    
    # 申万一级行业列表
    industries = [
        ('农林牧渔', '801010.SI'),
        ('采掘', '801020.SI'),
        ('化工', '801030.SI'),
        ('钢铁', '801040.SI'),
        ('有色金属', '801050.SI'),
        ('电子', '801080.SI'),
        ('汽车', '801110.SI'),
        ('家用电器', '801130.SI'),
        ('食品饮料', '801120.SI'),
        ('纺织服装', '801140.SI'),
        ('轻工制造', '801150.SI'),
        ('医药生物', '801160.SI'),
        ('公用事业', '801170.SI'),
        ('交通运输', '801180.SI'),
        ('房地产', '801200.SI'),
        ('商业贸易', '801210.SI'),
        ('休闲服务', '801220.SI'),
        ('银行', '801230.SI'),
        ('非银金融', '801240.SI'),
        ('建筑材料', '801250.SI'),
        ('建筑装饰', '801260.SI'),
        ('电气设备', '801270.SI'),
        ('国防军工', '801280.SI'),
        ('计算机', '801290.SI'),
        ('传媒', '801300.SI'),
        ('通信', '801310.SI'),
        ('机械设备', '801320.SI'),
    ]
    
    all_constituents = []
    success_count = 0
    fail_count = 0
    
    for industry_name, symbol in industries:
        print(f"\n正在获取 {industry_name} 行业成分股...")
        
        df = get_sw_industry_constituents(symbol, industry_name)
        
        if df is not None and len(df) > 0:
            df['申万一级'] = industry_name
            all_constituents.append(df)
            print(f"  ✓ 获取成功: {len(df)} 只股票")
            success_count += 1
        else:
            fail_count += 1
        
        # 延迟，避免请求过快
        time.sleep(0.5)
    
    if all_constituents:
        # 合并所有数据
        result = pd.concat(all_constituents, ignore_index=True)
        
        print("\n" + "=" * 60)
        print("获取完成")
        print("=" * 60)
        print(f"成功行业: {success_count}")
        print(f"失败行业: {fail_count}")
        print(f"总股票数: {len(result)}")
        
        return result
    else:
        print("\n未获取到任何数据")
        return None


def save_to_json(df, output_file):
    """
    保存为 JSON 文件
    """
    if df is None or len(df) == 0:
        print("无数据可保存")
        return
    
    # 转换为 JSON 格式
    data = df.to_dict(orient='records')
    
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    
    print(f"\n已保存到: {output_file}")


def save_to_csv(df, output_file):
    """
    保存为 CSV 文件
    """
    if df is None or len(df) == 0:
        print("无数据可保存")
        return
    
    df.to_csv(output_file, index=False, encoding='utf-8-sig')
    print(f"\n已保存到: {output_file}")


def main():
    """
    主函数
    """
    print("\n开始获取申万行业成分股...\n")
    
    # 获取所有成分股
    result = fetch_all_constituents()
    
    if result is not None:
        # 保存为 JSON
        json_file = Path(__file__).parent / 'sw_industry_constituents.json'
        save_to_json(result, json_file)
        
        # 保存为 CSV
        csv_file = Path(__file__).parent / 'sw_industry_constituents.csv'
        save_to_csv(result, csv_file)
        
        print("\n" + "=" * 60)
        print("申万行业成分股获取完成!")
        print("=" * 60)
    else:
        print("\n获取失败，请检查网络连接")


if __name__ == "__main__":
    main()
