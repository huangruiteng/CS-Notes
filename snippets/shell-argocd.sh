#!/bin/bash

# ArgoCD CLI 常用命令备忘清单

# 1. 登录 ArgoCD
# 默认用户名为 admin，密码通常是 argocd-server pod 的名称或初始生成的 secret
# argocd login <ARGOCD_SERVER_IP> --username admin --password <PASSWORD> --insecure

# 2. 列出所有应用
argocd app list

# 3. 查看应用详情
# argocd app get <APP_NAME>
# 示例: argocd app get my-app

# 4. 手动同步应用 (Trigger Sync)
# argocd app sync <APP_NAME>
# 示例: argocd app sync my-app

# 5. 硬刷新 (不使用缓存，强制从 Git 拉取最新配置)
# argocd app get <APP_NAME> --refresh

# 6. 查看应用资源树
# argocd app resources <APP_NAME>

# 7. 查看应用日志 (如果 ArgoCD 有权限访问 Pod 日志)
# argocd app logs <APP_NAME>

# 8. 创建应用 (命令行方式，通常推荐用 YAML)
# argocd app create guestbook \
#    --repo https://github.com/argoproj/argocd-example-apps.git \
#    --path guestbook \
#    --dest-server https://kubernetes.default.svc \
#    --dest-namespace default

# 9. 删除应用 (级联删除 K8s 资源)
# argocd app delete <APP_NAME> --cascade

# 10. 排查问题：查看 Controller 日志
# kubectl logs -n argocd -l app.kubernetes.io/name=argocd-application-controller -f

# 11. 处理卡在 Terminating 的应用
# 如果应用无法删除，通常是因为 finalizer。可以 patch 掉 finalizer
# kubectl patch app <APP_NAME> -n argocd -p '{"metadata": {"finalizers": []}}' --type merge
