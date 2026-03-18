#!/bin/bash
# 自动更新数据 - 重试脚本（8点执行）
# 检查7点的任务是否成功，如果失败则重试

SUCCESS_FLAG="/tmp/auto_update_success_$(date +%Y%m%d)"
LOG_FILE="/app/work/logs/bypass/auto_update.log"

# 检查今天是否已经成功
if [ -f "$SUCCESS_FLAG" ]; then
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] 今天已经成功更新，跳过重试" >> "$LOG_FILE"
    exit 0
fi

echo "[$(date '+%Y-%m-%d %H:%M:%S')] 检测到上次更新失败，开始重试..." >> "$LOG_FILE"

# 执行更新脚本
cd /workspace/projects
python3 server/auto_update_data.py

# 检查执行结果
if [ $? -eq 0 ]; then
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] 重试成功" >> "$LOG_FILE"
    touch "$SUCCESS_FLAG"
    exit 0
else
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] 重试失败" >> "$LOG_FILE"
    exit 1
fi
