#!/bin/bash
# ARM64 构建实时监控脚本

OUTPUT_FILE="C:\Users\Administrator\AppData\Local\Temp\claude\C--Users-Administrator\8994aac2-31bf-45d3-b05a-19ad13f19e9f\tasks\ba4zgixyw.output"

clear
echo "========================================"
echo "ARM64 构建实时监控"
echo "开始时间: $(date '+%Y-%m-%d %H:%M:%S')"
echo "========================================"
echo ""

while true; do
    if [ -f "$OUTPUT_FILE" ]; then
        # 清屏并显示最新内容
        clear
        echo "========================================"
        echo "ARM64 构建进度 - $(date '+%H:%M:%S')"
        echo "========================================"
        echo ""

        # 显示最后 40 行
        tail -40 "$OUTPUT_FILE"

        echo ""
        echo "========================================"

        # 检查关键进度
        if grep -q "\[1/5\]" "$OUTPUT_FILE"; then
            echo "✓ 阶段 1/5: 清理完成"
        fi

        if grep -q "\[2/5\]" "$OUTPUT_FILE"; then
            echo "✓ 阶段 2/5: Buildx 配置完成"
        fi

        if grep -q "\[3/5\]" "$OUTPUT_FILE"; then
            echo "⏳ 阶段 3/5: Docker 构建进行中..."
        fi

        if grep -q "\[4/5\]" "$OUTPUT_FILE"; then
            echo "✓ 阶段 4/5: DEB 包提取完成"
        fi

        if grep -q "\[5/5\]" "$OUTPUT_FILE"; then
            echo "✅ 阶段 5/5: 构建完成！"
            break
        fi

        if grep -q "ERROR" "$OUTPUT_FILE"; then
            echo "❌ 检测到错误"
            break
        fi

        echo ""
        echo "按 Ctrl+C 退出监控（构建继续在后台运行）"
    else
        echo "等待构建开始..."
    fi

    sleep 10
done

echo ""
echo "监控结束"
