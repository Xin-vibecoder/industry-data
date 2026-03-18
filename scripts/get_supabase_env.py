#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
获取Supabase环境变量
"""
import sys
import os
from pathlib import Path

# 添加项目路径到sys.path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root / "server"))

from src.storage.database.supabase_client import get_supabase_credentials

def main():
    try:
        url, key = get_supabase_credentials()
        print(f"COZE_SUPABASE_URL={url}")
        print(f"COZE_SUPABASE_ANON_KEY={key}")
    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)

if __name__ == "__main__":
    main()
