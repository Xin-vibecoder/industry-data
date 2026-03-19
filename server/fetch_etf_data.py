#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
获取A股ETF基金数据
从2024年1月1日开始获取所有ETF的历史行情数据
"""
import sys
import os
from pathlib import Path
from datetime import datetime, timedelta
import time

project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root / "server"))

import akshare as ak
import pandas as pd
import numpy as np
from src.storage.database.supabase_client import get_supabase_client

LOG_FILE = "/app/work/logs/bypass/etf_update.log"

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


def fetch_etf_list(client):
    """
    获取ETF列表
    """
    log("=" * 60)
    log("步骤1: 获取ETF列表")
    log("=" * 60)
    
    try:
        # 使用新浪接口获取ETF列表（更稳定）
        df = ak.fund_etf_category_sina(symbol="ETF基金")
        
        if df is None or len(df) == 0:
            log("未获取到ETF数据")
            return []
        
        log(f"获取到 {len(df)} 只ETF")
        
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
            if '货币' in name or '理财' in name or '银华' in name and '货币' in name:
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
            # 先清空旧数据
            client.table('etf_info').delete().neq('id', 0).execute()
            
            # 分批插入
            batch_size = 500
            for i in range(0, len(etf_list), batch_size):
                batch = etf_list[i:i+batch_size]
                client.table('etf_info').insert(batch).execute()
            
            log(f"✓ 成功存储 {len(etf_list)} 只ETF信息")
        
        return etf_list
        
    except Exception as e:
        log(f"获取ETF列表失败: {e}")
        import traceback
        traceback.print_exc()
        return []


def fetch_etf_history(client, etf_list, start_date='20240101'):
    """
    获取ETF历史行情数据
    """
    log("=" * 60)
    log(f"步骤2: 获取ETF历史行情数据（从{start_date}开始）")
    log("=" * 60)
    
    end_date = datetime.now().strftime('%Y%m%d')
    total_count = len(etf_list)
    success_count = 0
    fail_count = 0
    total_records = 0
    
    for idx, etf in enumerate(etf_list):
        code = etf['code'].replace('sz', '').replace('sh', '')  # 去掉前缀
        name = etf['name']
        
        try:
            # 获取历史行情
            df = ak.fund_etf_hist_em(
                symbol=code,
                period='daily',
                start_date=start_date,
                end_date=end_date,
                adjust='qfq'  # 前复权
            )
            
            if df is None or len(df) == 0:
                log(f"  [{idx+1}/{total_count}] {code} {name}: 无历史数据")
                time.sleep(0.1)
                continue
            
            # 准备数据记录
            data_records = []
            for _, row in df.iterrows():
                trade_date = row.get('日期', row.get('date', ''))
                if isinstance(trade_date, (pd.Timestamp, datetime)):
                    trade_date = trade_date.strftime('%Y-%m-%d')
                elif not isinstance(trade_date, str):
                    trade_date = str(trade_date)
                
                # 格式化日期
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
                
                # 分批插入（每批500条）
                batch_size = 500
                for i in range(0, len(data_records), batch_size):
                    batch = data_records[i:i+batch_size]
                    client.table('etf_daily_data').insert(batch).execute()
                
                total_records += len(data_records)
                success_count += 1
                log(f"  [{idx+1}/{total_count}] {code} {name}: {len(data_records)} 条 ✓")
            
            # 延迟避免请求过快
            time.sleep(0.3)
            
        except Exception as e:
            fail_count += 1
            log(f"  [{idx+1}/{total_count}] {code} {name}: 失败 - {str(e)[:50]}")
            time.sleep(0.5)
            continue
    
    log("=" * 60)
    log(f"历史数据获取完成: 成功 {success_count}, 失败 {fail_count}, 总记录 {total_records}")
    log("=" * 60)
    
    return total_records


def main():
    """主函数"""
    log("\n" + "=" * 60)
    log("ETF数据获取任务启动")
    log("=" * 60)
    
    try:
        # 初始化客户端
        client = get_supabase_client()
        log("✓ Supabase客户端初始化成功")
        
        # 获取ETF列表
        etf_list = fetch_etf_list(client)
        
        if not etf_list:
            log("未获取到ETF列表，任务结束")
            return 1
        
        # 获取历史行情数据
        fetch_etf_history(client, etf_list, start_date='20240101')
        
        log("\n" + "=" * 60)
        log("✓ ETF数据获取任务完成")
        log("=" * 60)
        
        return 0
        
    except Exception as e:
        log(f"任务执行失败: {e}")
        import traceback
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    sys.exit(main())
