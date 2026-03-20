#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
检查今天是否需要更新数据
- 如果是主更新时段(UTC 12:00/北京时间20:00)，总是更新
- 如果是重试时段，检查今天是否已有数据
"""
import os
import sys
from pathlib import Path
from datetime import datetime, timezone, timedelta

# 添加项目路径到sys.path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from server.src.storage.database.supabase_client import get_supabase_client


def main():
    # 获取当前UTC时间
    now_utc = datetime.now(timezone.utc)
    current_hour = now_utc.hour
    
    # 北京时间 = UTC + 8
    beijing_tz = timezone(timedelta(hours=8))
    today_beijing = datetime.now(beijing_tz).strftime('%Y-%m-%d')
    
    # 检查是否强制更新
    force_update = os.environ.get('FORCE_UPDATE', 'false').lower() == 'true'
    
    # 主更新时段: UTC 12:00 (北京时间 20:00)
    is_main_schedule = current_hour == 12
    
    if force_update:
        print(f"强制更新模式，开始更新...")
        with open(os.environ['GITHUB_OUTPUT'], 'a') as f:
            f.write('needed=true\n')
        return
    
    if is_main_schedule:
        print(f"主更新时段 (UTC {current_hour}:00)，开始更新...")
        with open(os.environ['GITHUB_OUTPUT'], 'a') as f:
            f.write('needed=true\n')
        return
    
    # 重试时段: 检查今天是否已有数据
    print(f"重试时段 (UTC {current_hour}:00)，检查今天是否已有数据...")
    
    try:
        client = get_supabase_client()
        result = client.table('industry_daily_data').select('date', count='exact').eq('date', today_beijing).execute()
        
        if result.count > 0:
            print(f"✓ 今天 ({today_beijing}) 已有 {result.count} 条数据，跳过更新")
            with open(os.environ['GITHUB_OUTPUT'], 'a') as f:
                f.write('needed=false\n')
        else:
            print(f"✗ 今天 ({today_beijing}) 暂无数据，开始更新...")
            with open(os.environ['GITHUB_OUTPUT'], 'a') as f:
                f.write('needed=true\n')
    except Exception as e:
        print(f"检查数据时出错: {e}")
        # 出错时仍然尝试更新
        with open(os.environ['GITHUB_OUTPUT'], 'a') as f:
            f.write('needed=true\n')


if __name__ == "__main__":
    main()
