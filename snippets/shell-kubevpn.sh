#!/bin/bash

# 问题：kubevpn 连不上 nacos (Traffic Manager 有 Terminating 状态的旧 Pod)
# 现象：连接超时或无法解析服务
# 原因：kubevpn 的 traffic manager 存在未清理的 Terminating Pod，导致路由混乱
# 解法：强制清理旧 Pod -> 全局断开 -> 重新连接

echo "1. 强制删除 Terminating 状态的 kubevpn pod..."
# 筛选所有 namespace 下状态为 Terminating 的 kubevpn 相关 pod 并强制删除
kubectl get pods -A | grep kubevpn | grep Terminating | awk '{print "kubectl delete pod " $2 " -n " $1 " --force --grace-period=0"}' | sh

echo "2. 断开所有 kubevpn 连接..."
kubevpn disconnect --all

echo "3. 准备重连..."
echo "请执行你的连接命令，例如: kubevpn connect ..."
# 或者如果配置了 alias:
# kubevpn alias
