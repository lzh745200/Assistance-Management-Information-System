#!/bin/bash
# 蓝绿部署流量切换脚本

set -e

NAMESPACE="rural-revitalization"
SERVICE_NAME="backend"

echo "蓝绿部署流量切换工具"
echo "===================="

# 获取当前活跃版本
get_active_version() {
    kubectl get svc $SERVICE_NAME -n $NAMESPACE -o jsonpath='{.spec.selector.version}' 2>/dev/null || echo "blue"
}

# 切换流量
switch_traffic() {
    local target_version=$1

    echo "切换流量到 $target_version 环境..."

    kubectl patch svc $SERVICE_NAME -n $NAMESPACE \
        -p '{"spec":{"selector":{"app":"backend","version":"'$target_version'"}}}'

    echo "流量切换完成"
}

# 健康检查
health_check() {
    local version=$1
    local max_attempts=10
    local attempt=1

    echo "检查 $version 环境健康状态..."

    while [ $attempt -le $max_attempts ]; do
        # 获取 Pod 状态
        ready_pods=$(kubectl get pods -n $NAMESPACE -l app=backend,version=$version \
            -o jsonpath='{range .items[*]}{.status.conditions[?(@.type=="Ready")].status}{"\n"}{end}' | grep -c "True" || echo "0")

        total_pods=$(kubectl get pods -n $NAMESPACE -l app=backend,version=$version --no-headers | wc -l)

        echo "尝试 $attempt/$max_attempts: $ready_pods/$total_pods Pods 就绪"

        if [ "$ready_pods" -eq "$total_pods" ] && [ "$total_pods" -gt 0 ]; then
            echo "健康检查通过"
            return 0
        fi

        sleep 5
        attempt=$((attempt + 1))
    done

    echo "健康检查失败"
    return 1
}

# 回滚ollback() {
    echo "执行回滚..."

    # 切换回另一个环境
    current_version=$(get_active_version)
    if [ "$current_version" = "blue" ]; then
        switch_traffic "green"
    else
        switch_traffic "blue"
    fi

    echo "回滚完成"
}

# 显示状态
show_status() {
    echo "当前部署状态:"
    echo "-------------"

    active_version=$(get_active_version)
    echo "活跃环境: $active_version"

    echo ""
    echo "Blue 环境 Pods:"
    kubectl get pods -n $NAMESPACE -l app=backend,version=blue --no-headers 2>/dev/null || echo "  无"

    echo ""
    echo "Green 环境 Pods:"
    kubectl get pods -n $NAMESPACE -l app=backend,version=green --no-headers 2>/dev/null || echo "  无"

    echo ""
    echo "Service 配置:"
    kubectl get svc $SERVICE_NAME -n $NAMESPACE -o jsonpath='{.spec.selector}' 2>/dev/null || echo "  无法获取"
}

# 主菜单
case "${1:-status}" in
    status)
        show_status
        ;;
    switch)
        target=${2:-}
        if [ -z "$target" ]; then
            echo "用法: $0 switch <blue|green>"
            exit 1
        fi
        switch_traffic $target
        ;;
    deploy)
        version=${2:-green}
        image_tag=${3:-latest}

        echo "部署到 $version 环境，镜像: $image_tag"

        # 更新镜像
        kubectl set image deployment/backend-$version \
            backend=rural-revitalization/backend:$image_tag \
            -n $NAMESPACE

        # 等待部署完成
        kubectl rollout status deployment/backend-$version -n $NAMESPACE --timeout=300s

        # 健康检查
        if health_check $version; then
            echo "部署成功，准备切换流量"
            read -p "是否切换流量到 $version? (y/n) " confirm
            if [ "$confirm" = "y" ]; then
                switch_traffic $version
            fi
        else
            echo "部署失败，请检查日志"
            exit 1
        fi
        ;;
    rollback)
        rollback
        ;;
    health)
        version=${2:-$(get_active_version)}
        health_check $version
        ;;
    *)
        echo "用法: $0 <command> [options]"
        echo ""
        echo "Commands:"
        echo "  status              显示当前状态"
        echo "  switch <version>    切换流量到指定版本"
        echo "  deploy <version> <image>  部署并切换流量"
        echo "  rollback            回滚到之前的环境"
        echo "  health [version]    检查指定版本健康状态"
        exit 1
        ;;
esac
