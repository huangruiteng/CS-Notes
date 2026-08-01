#!/bin/bash
# Git Sync 脚本 - 智能处理各种 Git 同步场景
# 支持：本地有 commit + 远端有 commit 的冲突处理
# 提供多种冲突解决策略

# 设置 locale，确保能正确处理中文文件名
export LANG=en_US.UTF-8
export LC_ALL=en_US.UTF-8
export LC_CTYPE=en_US.UTF-8

# 配置
REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
LOG_DIR="$REPO_ROOT/.trae/logs"
LOG_FILE="$LOG_DIR/git-sync-$(date +%Y%m%d).log"
DEFAULT_BRANCH="master"
STRATEGY="${1:-auto}"  # 可选：auto, rebase, merge, stash, ask

# 创建日志目录
mkdir -p "$LOG_DIR"

# 日志函数
log() {
    local level="$1"
    shift
    local message="$*"
    local timestamp="$(date '+%Y-%m-%d %H:%M:%S')"
    echo "[$timestamp] [$level] $message" | tee -a "$LOG_FILE"
}

# 错误处理函数
error_exit() {
    log "ERROR" "$1"
    exit 1
}

# 检查 git 仓库状态
check_git_status() {
    cd "$REPO_ROOT" || return 1
    
    local status_output=$(git status --porcelain)
    if [ -n "$status_output" ]; then
        log "INFO" "检测到未提交的更改:"
        echo "$status_output" | while IFS= read -r line; do
            log "INFO" "  $line"
        done
        return 1
    fi
    return 0
}

# 检查是否有本地 commit 但未 push
has_unpushed_commits() {
    cd "$REPO_ROOT" || return 1
    
    local current_branch=$(git rev-parse --abbrev-ref HEAD)
    local unpushed=$(git log "origin/$current_branch..HEAD" --oneline 2>/dev/null)
    
    if [ -n "$unpushed" ]; then
        log "INFO" "检测到本地有 $current_branch 分支上未 push 的 commit:"
        echo "$unpushed" | while IFS= read -r line; do
            log "INFO" "  $line"
        done
        return 0
    fi
    return 1
}

# 检查是否有远端 commit 但未 pull
has_remote_commits() {
    cd "$REPO_ROOT" || return 1
    
    local current_branch=$(git rev-parse --abbrev-ref HEAD)
    
    # 先 fetch 一下以获取最新的远程状态
    git fetch origin >> "$LOG_FILE" 2>&1
    
    local remote_commits=$(git log "HEAD..origin/$current_branch" --oneline 2>/dev/null)
    
    if [ -n "$remote_commits" ]; then
        log "INFO" "检测到远端有 $current_branch 分支上未 pull 的 commit:"
        echo "$remote_commits" | while IFS= read -r line; do
            log "INFO" "  $line"
        done
        return 0
    fi
    return 1
}

# 检查是否有冲突
check_conflicts() {
    cd "$REPO_ROOT" || return 1
    
    if git ls-files -u | grep -q .; then
        log "ERROR" "检测到 Git 合并冲突！"
        log "ERROR" "冲突文件列表："
        git ls-files -u | awk '{print $4}' | sort -u | while IFS= read -r file; do
            log "ERROR" "  - $file"
        done
        return 1
    fi
    return 0
}

# 策略1: Rebase（推荐用于个人开发）
strategy_rebase() {
    log "INFO" "使用 rebase 策略..."
    cd "$REPO_ROOT" || return 1
    
    local current_branch=$(git rev-parse --abbrev-ref HEAD)
    
    if git rebase "origin/$current_branch"; then
        log "SUCCESS" "Rebase 成功！"
        return 0
    else
        log "ERROR" "Rebase 失败，可能存在冲突"
        git rebase --abort 2>/dev/null
        return 1
    fi
}

# 策略2: Merge（创建合并 commit）
strategy_merge() {
    log "INFO" "使用 merge 策略..."
    cd "$REPO_ROOT" || return 1
    
    local current_branch=$(git rev-parse --abbrev-ref HEAD)
    
    if git merge "origin/$current_branch" --no-edit; then
        log "SUCCESS" "Merge 成功！"
        return 0
    else
        log "ERROR" "Merge 失败，可能存在冲突"
        git merge --abort 2>/dev/null
        return 1
    fi
}

# 策略3: Stash（暂存本地更改，先 pull，再恢复）
strategy_stash() {
    log "INFO" "使用 stash 策略..."
    cd "$REPO_ROOT" || return 1
    
    local current_branch=$(git rev-parse --abbrev-ref HEAD)
    
    # 暂存本地 commit（使用 git reset --soft + stash）
    local stash_name="git-sync-$(date +%Y%m%d-%H%M%S)"
    git reset --soft "origin/$current_branch" 2>/dev/null
    git stash push -m "$stash_name" >> "$LOG_FILE" 2>&1
    
    # 先 pull
    if git pull origin "$current_branch"; then
        log "INFO" "Pull 成功，尝试恢复 stash..."
        # 恢复 stash
        if git stash pop; then
            log "SUCCESS" "Stash 恢复成功！"
            log "INFO" "注意：你需要重新 commit 你的更改"
            return 0
        else
            log "WARN" "Stash 恢复可能有冲突"
            check_conflicts
            return 1
        fi
    else
        log "ERROR" "Pull 失败"
        git stash pop 2>/dev/null  # 尝试恢复
        return 1
    fi
}

# 策略4: Auto（自动选择最佳策略）
strategy_auto() {
    log "INFO" "使用 auto 策略，自动选择最佳方案..."
    
    # 尝试 rebase（优先）
    if strategy_rebase; then
        return 0
    fi
    
    log "WARN" "Rebase 失败，尝试 merge..."
    
    # 尝试 merge
    if strategy_merge; then
        return 0
    fi
    
    log "WARN" "Merge 失败，尝试 stash..."
    
    # 最后尝试 stash
    if strategy_stash; then
        return 0
    fi
    
    log "ERROR" "所有策略都失败，请手动处理"
    return 1
}

# 智能同步主流程
git_sync() {
    cd "$REPO_ROOT" || error_exit "无法进入仓库目录"
    
    log "INFO" "========================================"
    log "INFO" "Git Sync 开始执行"
    log "INFO" "策略: $STRATEGY"
    log "INFO" "========================================"
    
    local current_branch=$(git rev-parse --abbrev-ref HEAD)
    log "INFO" "当前分支: $current_branch"
    
    # 步骤1: 获取远程更新
    log "INFO" "步骤 1/5: 获取远程更新"
    git fetch origin >> "$LOG_FILE" 2>&1 || {
        log "WARN" "获取远程更新失败，继续检查本地状态..."
    }
    
    # 步骤2: 检查各种状态
    log "INFO" "步骤 2/5: 检查 Git 状态"
    
    local has_uncommitted=0
    local has_unpushed=0
    local has_remote=0
    
    if ! check_git_status; then
        has_uncommitted=1
    fi
    
    if has_unpushed_commits; then
        has_unpushed=1
    fi
    
    if has_remote_commits; then
        has_remote=1
    fi
    
    # 步骤3: 根据状态选择操作
    log "INFO" "步骤 3/5: 分析同步状态"
    
    if [ $has_uncommitted -eq 0 ] && [ $has_unpushed -eq 0 ] && [ $has_remote -eq 0 ]; then
        log "SUCCESS" "一切都是最新的，无需同步"
        return 0
    fi
    
    if [ $has_uncommitted -eq 1 ]; then
        log "WARN" "检测到未提交的更改"
        log "INFO" "建议：先提交或 stash 你的更改"
    fi
    
    if [ $has_unpushed -eq 1 ] && [ $has_remote -eq 0 ]; then
        log "INFO" "只有本地 commit，直接 push"
        if git push origin "$current_branch"; then
            log "SUCCESS" "Push 成功！"
            return 0
        else
            log "ERROR" "Push 失败"
            return 1
        fi
    fi
    
    if [ $has_unpushed -eq 0 ] && [ $has_remote -eq 1 ]; then
        log "INFO" "只有远端 commit，直接 pull"
        if git pull origin "$current_branch"; then
            log "SUCCESS" "Pull 成功！"
            return 0
        else
            log "ERROR" "Pull 失败"
            check_conflicts
            return 1
        fi
    fi
    
    # 步骤4: 处理复杂情况（本地和远端都有 commit）
    log "WARN" "步骤 4/5: 检测到本地和远端都有 commit！"
    log "INFO" "这是一个需要谨慎处理的情况"
    
    case "$STRATEGY" in
        rebase)
            strategy_rebase
            ;;
        merge)
            strategy_merge
            ;;
        stash)
            strategy_stash
            ;;
        auto)
            strategy_auto
            ;;
        ask)
            log "INFO" "ask 模式：请手动选择策略"
            log "INFO" "可用策略："
            log "INFO" "  rebase - 将本地 commit 放到远端 commit 之上（推荐）"
            log "INFO" "  merge  - 创建合并 commit"
            log "INFO" "  stash  - 暂存本地更改，先 pull，再恢复"
            log "INFO" "  auto   - 自动尝试各种策略"
            return 1
            ;;
        *)
            log "ERROR" "未知策略: $STRATEGY"
            return 1
            ;;
    esac
    
    local strategy_result=$?
    
    # 步骤5: 如果策略成功，尝试 push
    if [ $strategy_result -eq 0 ]; then
        log "INFO" "步骤 5/5: 尝试推送"
        if git push origin "$current_branch"; then
            log "SUCCESS" "同步完成！"
            return 0
        else
            log "WARN" "Push 失败，可能需要再次同步"
            return 1
        fi
    fi
    
    return $strategy_result
}

# 显示帮助
show_help() {
    echo "Git Sync - 智能 Git 同步工具"
    echo ""
    echo "用法: $0 [策略]"
    echo ""
    echo "可用策略："
    echo "  auto   - 自动选择最佳策略（默认）"
    echo "  rebase - 将本地 commit 放到远端 commit 之上（推荐用于个人开发）"
    echo "  merge  - 创建合并 commit"
    echo "  stash  - 暂存本地更改，先 pull，再恢复"
    echo "  ask    - 显示帮助信息，不执行操作"
    echo ""
    echo "示例："
    echo "  $0              # 自动策略"
    echo "  $0 rebase       # 使用 rebase"
    echo "  $0 merge        # 使用 merge"
    echo ""
    echo "日志文件: $LOG_FILE"
}

# 主函数
main() {
    if [ "$STRATEGY" = "help" ] || [ "$STRATEGY" = "--help" ] || [ "$STRATEGY" = "-h" ]; then
        show_help
        exit 0
    fi
    
    git_sync
    local sync_result=$?
    
    log "INFO" "========================================"
    if [ $sync_result -eq 0 ]; then
        log "SUCCESS" "Git Sync 执行成功"
    else
        log "WARN" "Git Sync 执行完成，但可能需要手动处理"
    fi
    log "INFO" "日志文件: $LOG_FILE"
    log "INFO" "========================================"
    
    exit $sync_result
}

# 运行主函数
main
