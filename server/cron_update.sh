#!/bin/bash
# 自动更新数据 - 定时任务脚本
# 成功标志文件
SUCCESS_FLAG="/tmp/auto_update_success_$(date +%Y%m%d)"
LOG_FILE="/app/work/logs/bypass/auto_update.log"

# 执行更新脚本
cd /workspace/projects
python3 server/auto_update_data.py

# 检查执行结果
if [ $? -eq 0 ]; then
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] 自动更新成功" >> "$LOG_FILE"
    touch "$SUCCESS_FLAG"
    exit 0
else
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] 自动更新失败" >> "$LOG_FILE"
    exit 1
fi
