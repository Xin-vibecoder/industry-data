#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
测试AKShare同花顺行业数据接口
"""
import akshare as ak
import pandas as pd
from datetime import datetime

def test_ths_industry_data():
    """测试获取同花顺行业数据"""
    print("=" * 60)
    print("测试1: 获取同花顺行业板块列表")
    print("=" * 60)
    
    try:
        # 获取同花顺行业板块列表
        industry_list = ak.stock_board_industry_name_ths()
        print(f"\n行业板块数量: {len(industry_list)}")
        print("\n前5个行业板块:")
        print(industry_list.head())
        print("\n列名:")
        print(industry_list.columns.tolist())
    except Exception as e:
        print(f"获取行业板块列表失败: {e}")
    
    print("\n" + "=" * 60)
    print("测试2: 获取具体行业的历史数据")
    print("=" * 60)
    
    try:
        # 获取某个行业的历史数据（例如：计算机）
        # 先获取行业列表
        industry_list = ak.stock_board_industry_name_ths()
        
        # 选择第一个行业进行测试
        if len(industry_list) > 0:
            first_industry = industry_list.iloc[0]['name']
            print(f"\n测试行业: {first_industry}")
            
            # 获取该行业的历史数据
            industry_data = ak.stock_board_industry_index_ths(
                symbol=first_industry,
                start_date="20240101",
                end_date=datetime.now().strftime("%Y%m%d")
            )
            
            print(f"\n数据行数: {len(industry_data)}")
            print("\n前5行数据:")
            print(industry_data.head())
            print("\n列名:")
            print(industry_data.columns.tolist())
            print("\n数据类型:")
            print(industry_data.dtypes)
    except Exception as e:
        print(f"获取行业历史数据失败: {e}")

if __name__ == "__main__":
    test_ths_industry_data()
