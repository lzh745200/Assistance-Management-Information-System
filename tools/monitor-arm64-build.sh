#!/bin/bash
# ARM64 构建进度监控

OUTPUT_FILE="C:\Users\Administrator\AppData\Local\Temp\claude\C--Users-Administrator\8994aac2-31bf-45d3-b05a-19ad13f19e9f\tasks\b02x4040r.output"

echo "========================================"
echo "ARM64 构建进度监控"
echo "========================================"
echo ""

if [ -f "$OUTPUT_FILE" ]; then
    echo "最新输出:"
    echo "----------------------------------------"
    tail -30 "$OUTPUT_FILE"
    echo "----------------------------------------"
    echo ""

    # 检查关键进度标记
    if grep -q "\[1/5\]" "$OUTPUT_FILE"; then
        echo "✓ 阶段 1: 清理完成"
    fi

    if grep -q "\[2/5\]" "$OUTPUT_FILE"; then
        echo "✓ 阶段 2: Buildx 配置完成"
    fi

    if grep -q "\[3/5\]" "$OUTPUT_FILE"; then
        echo "⏳ 阶段 3: Docker 构建进行中..."
    fi

    if grep -q "\[4/5\]" "$OUTPUT_FILE"; then
        echo "✓ 阶段 4: DEB 包提取完成"
    fi

    if grep -q "\[5/5\]" "$OUTPUT_FILE"; then
        echo "✓ 阶段 5: 构建完成！"
    fi

    if grep -q "错误" "$OUTPUT_FILE"; then
        echo "⚠️  检测到错误，请查看详细日志"
    fi
else
    echo "输出文件尚未生成，构建刚开始..."
fi

echo ""
echo "========================================"
