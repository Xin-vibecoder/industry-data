#!/bin/bash
# 启动定时任务调度器

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
LOG_FILE="/app/work/logs/bypass/scheduler.log"
PID_FILE="/tmp/scheduler.pid"

# 检查是否已经在运行
if [ -f "$PID_FILE" ]; then
    PID=$(cat "$PID_FILE")
    if ps -p "$PID" > /dev/null 2>&1; then
        echo "调度器已在运行中 (PID: $PID)"
        exit 0
    else
        echo "清理过期的PID文件"
        rm -f "$PID_FILE"
    fi
fi

# 启动调度器
echo "启动定时任务调度器..."
nohup python3 "$SCRIPT_DIR/scheduler.py" >> "$LOG_FILE" 2>&1 &

# 等待启动
sleep 2

# 检查是否启动成功
if [ -f "$PID_FILE" ]; then
    PID=$(cat "$PID_FILE")
    echo "✓ 调度器启动成功 (PID: $PID)"
    echo "日志文件: $LOG_FILE"
else
    echo "✗ 调度器启动失败，请检查日志: $LOG_FILE"
    exit 1
fi
