#!/bin/bash
# 停止定时任务调度器

PID_FILE="/tmp/scheduler.pid"

if [ -f "$PID_FILE" ]; then
    PID=$(cat "$PID_FILE")
    if ps -p "$PID" > /dev/null 2>&1; then
        echo "停止调度器 (PID: $PID)..."
        kill "$PID"
        
        # 等待进程结束
        for i in {1..10}; do
            if ! ps -p "$PID" > /dev/null 2>&1; then
                echo "✓ 调度器已停止"
                rm -f "$PID_FILE"
                exit 0
            fi
            sleep 1
        done
        
        # 强制结束
        echo "强制结束调度器..."
        kill -9 "$PID"
        rm -f "$PID_FILE"
        echo "✓ 调度器已强制停止"
    else
        echo "调度器未运行"
        rm -f "$PID_FILE"
    fi
else
    echo "未找到PID文件，调度器可能未运行"
fi
