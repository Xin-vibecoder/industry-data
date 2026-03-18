#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
定时任务调度器
替代crontab，实现每天定时执行数据更新
"""
import sys
import os
from pathlib import Path
import time
from datetime import datetime
import schedule
import threading
import subprocess

# 添加项目路径到sys.path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root / "server"))

# 日志文件
LOG_FILE = "/app/work/logs/bypass/scheduler.log"
PID_FILE = "/tmp/scheduler.pid"


def log(message):
    """记录日志"""
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    log_message = f"[{timestamp}] {message}"
    print(log_message)
    
    # 写入日志文件
    os.makedirs(os.path.dirname(LOG_FILE), exist_ok=True)
    with open(LOG_FILE, "a", encoding="utf-8") as f:
        f.write(log_message + "\n")


def run_update():
    """执行更新任务"""
    log("=" * 60)
    log("开始执行定时更新任务")
    log("=" * 60)
    
    try:
        # 执行更新脚本
        result = subprocess.run(
            ["python3", str(project_root / "server" / "auto_update_data.py")],
            capture_output=True,
            text=True,
            timeout=1800  # 30分钟超时
        )
        
        if result.returncode == 0:
            log("✓ 更新任务执行成功")
            log(result.stdout)
        else:
            log("✗ 更新任务执行失败")
            log(f"错误输出: {result.stderr}")
            
            # 标记失败，等待重试
            with open("/tmp/auto_update_failed", "w") as f:
                f.write(datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
        
    except subprocess.TimeoutExpired:
        log("✗ 更新任务超时")
    except Exception as e:
        log(f"✗ 更新任务异常: {e}")


def run_retry():
    """执行重试任务"""
    log("=" * 60)
    log("检查是否需要重试")
    log("=" * 60)
    
    # 检查今天是否已经成功
    success_flag = f"/tmp/auto_update_success_{datetime.now().strftime('%Y%m%d')}"
    if os.path.exists(success_flag):
        log("今天已经成功更新，跳过重试")
        return
    
    # 检查是否有失败标记
    if not os.path.exists("/tmp/auto_update_failed"):
        log("没有失败标记，跳过重试")
        return
    
    # 检查失败时间是否是今天
    with open("/tmp/auto_update_failed", "r") as f:
        fail_time = f.read().strip()
    
    if fail_time.startswith(datetime.now().strftime("%Y-%m-%d")):
        log(f"检测到今天 {fail_time} 更新失败，开始重试...")
        run_update()
    else:
        log("失败标记不是今天的，跳过重试")


def clear_flags():
    """清除标记文件"""
    log("清除旧的标记文件...")
    
    # 清除成功标记
    success_flag = f"/tmp/auto_update_success_{datetime.now().strftime('%Y%m%d')}"
    if os.path.exists(success_flag):
        os.remove(success_flag)
    
    # 清除失败标记
    if os.path.exists("/tmp/auto_update_failed"):
        os.remove("/tmp/auto_update_failed")
    
    log("✓ 标记文件清除完成")


def main():
    """主函数"""
    log("\n" + "=" * 60)
    log("定时任务调度器启动")
    log("=" * 60)
    
    # 写入PID文件
    with open(PID_FILE, "w") as f:
        f.write(str(os.getpid()))
    
    # 配置定时任务
    schedule.every().day.at("19:00").do(run_update)  # 每天19:00执行
    schedule.every().day.at("20:00").do(run_retry)   # 每天20:00重试
    schedule.every().day.at("00:05").do(clear_flags) # 每天凌晨清除标记
    
    log("✓ 定时任务配置完成:")
    log("  - 19:00 执行数据更新")
    log("  - 20:00 重试（如果失败）")
    log("  - 00:05 清除标记文件")
    
    # 启动调度器
    log("\n开始监听定时任务...")
    
    try:
        while True:
            schedule.run_pending()
            time.sleep(60)  # 每分钟检查一次
    except KeyboardInterrupt:
        log("\n接收到中断信号，停止调度器")
    except Exception as e:
        log(f"\n调度器异常: {e}")
        import traceback
        traceback.print_exc()
    finally:
        # 清理PID文件
        if os.path.exists(PID_FILE):
            os.remove(PID_FILE)
        log("调度器已停止")


if __name__ == "__main__":
    main()
