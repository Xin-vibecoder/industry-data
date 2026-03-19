#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
创建ETF相关数据表
"""
import sys
from pathlib import Path

project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root / "server"))

from src.storage.database.supabase_client import get_supabase_client

# ETF基金基础信息表
CREATE_ETF_INFO_TABLE = """
CREATE TABLE IF NOT EXISTS etf_info (
    id BIGSERIAL PRIMARY KEY,
    code VARCHAR(20) UNIQUE NOT NULL,           -- ETF代码
    name VARCHAR(100),                           -- ETF名称
    type VARCHAR(50),                            -- ETF类型（股票型、债券型、货币型、商品型等）
    exchange VARCHAR(20),                        -- 交易所（SH/SZ）
    list_date DATE,                              -- 上市日期
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_etf_info_code ON etf_info(code);
CREATE INDEX IF NOT EXISTS idx_etf_info_type ON etf_info(type);
"""

# ETF每日行情数据表
CREATE_ETF_DAILY_TABLE = """
CREATE TABLE IF NOT EXISTS etf_daily_data (
    id BIGSERIAL PRIMARY KEY,
    etf_code VARCHAR(20) NOT NULL,               -- ETF代码
    trade_date DATE NOT NULL,                    -- 交易日期
    open_price DECIMAL(18,4),                    -- 开盘价
    high_price DECIMAL(18,4),                    -- 最高价
    low_price DECIMAL(18,4),                     -- 最低价
    close_price DECIMAL(18,4),                   -- 收盘价
    volume BIGINT,                               -- 成交量
    amount DECIMAL(20,2),                        -- 成交额
    change_pct DECIMAL(10,4),                    -- 涨跌幅
    turnover_rate DECIMAL(10,4),                 -- 换手率
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(etf_code, trade_date)
);

CREATE INDEX IF NOT EXISTS idx_etf_daily_code ON etf_daily_data(etf_code);
CREATE INDEX IF NOT EXISTS idx_etf_daily_date ON etf_daily_data(trade_date);
CREATE INDEX IF NOT EXISTS idx_etf_daily_code_date ON etf_daily_data(etf_code, trade_date);
"""

def create_tables():
    """创建数据表"""
    client = get_supabase_client()
    
    print("创建ETF数据表...")
    
    # 使用RPC执行SQL
    try:
        # 注意：Supabase可能不直接支持执行DDL，需要通过其他方式
        # 这里我们先打印SQL，稍后手动执行或使用其他方式
        print("\n请在Supabase SQL编辑器中执行以下SQL：\n")
        print("=" * 60)
        print(CREATE_ETF_INFO_TABLE)
        print(CREATE_ETF_DAILY_TABLE)
        print("=" * 60)
        
    except Exception as e:
        print(f"创建表失败: {e}")


if __name__ == "__main__":
    create_tables()
