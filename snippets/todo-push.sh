#!/bin/bash
# Todo Push 脚本 - 生成变更摘要，供 AI 智能生成 commit message
# 严格控制 git add 范围，保护隐私
# 集成 OpenClaw 记忆文件同步功能

# 设置 locale，确保能正确处理中文文件名
export LANG=en_US.UTF-8
export LC_ALL=en_US.UTF-8
export LC_CTYPE=en_US.UTF-8

# 配置
REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
LOG_DIR="$REPO_ROOT/.trae/logs"
LOG_FILE="$LOG_DIR/todo-push-$(date +%Y%m%d).log"
DIFF_SUMMARY="$LOG_DIR/git-diff-summary-$(date +%Y%m%d-%H%M%S).md"
DEFAULT_BRANCH="master"

# OpenClaw 工作区路径（相对于 REPO_ROOT 的父目录）
OPENCLAW_WORKSPACE="$(dirname "$REPO_ROOT")"

# Git add 白名单：仅允许这些文件夹和文件
ALLOWED_FOLDERS=(
    "Notes/"
    ".trae/"
    "创作/"
    ".openclaw-memory/"
    "memory/"
)

# Git add 白名单文件：仅允许仓库根目录下的这些文件
ALLOWED_FILES=(
    "HEARTBEAT.md"
)

# Git add 黑名单：绝对禁止的文件夹
FORBIDDEN_FOLDERS=(
    "公司项目/"
)

# 排除的文件/文件夹（即使在白名单内也排除）
EXCLUDE_PATTERNS=(
    ".trae/logs/"
    "*.pyc"
    "__pycache__/"
    ".DS_Store"
    "venv/"
)

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

# 检查文件是否在允许范围内
is_file_allowed() {
    local file="$1"
    
    # 检查是否在黑名单中（绝对禁止）
    for forbidden in "${FORBIDDEN_FOLDERS[@]}"; do
        if [[ "$file" == "$forbidden"* ]]; then
            return 1
        fi
    done
    
    # 检查是否在白名单文件中（仓库根目录下的特定文件）
    for allowed_file in "${ALLOWED_FILES[@]}"; do
        if [[ "$file" == "$allowed_file" ]]; then
            # 检查是否需要排除
            for exclude in "${EXCLUDE_PATTERNS[@]}"; do
                if [[ "$file" == *"$exclude"* ]]; then
                    return 1
                fi
            done
            return 0
        fi
    done
    
    # 检查是否在白名单文件夹中
    local in_allowed=0
    for allowed in "${ALLOWED_FOLDERS[@]}"; do
        if [[ "$file" == "$allowed"* ]]; then
            in_allowed=1
            break
        fi
    done
    
    if [ $in_allowed -eq 0 ]; then
        return 1
    fi
    
    # 检查是否需要排除
    for exclude in "${EXCLUDE_PATTERNS[@]}"; do
        if [[ "$file" == *"$exclude"* ]]; then
            return 1
        fi
    done
    
    return 0
}

# 生成变更摘要文件
generate_diff_summary() {
    local allowed_files=("$@")
    
    log "INFO" "生成变更摘要: $DIFF_SUMMARY"
    
    {
        echo "# Git 变更摘要"
        echo ""
        echo "生成时间: $(date '+%Y-%m-%d %H:%M:%S')"
        echo ""
        echo "## 变更文件列表"
        echo ""
        
        # 显示每个文件的状态
        while read -r status file; do
            if is_file_allowed "$file"; then
                case "$status" in
                    M*) echo "- [修改] $file" ;;
                    A*) echo "- [新增] $file" ;;
                    D*) echo "- [删除] $file" ;;
                    R*) echo "- [重命名] $file" ;;
                    *) echo "- [$status] $file" ;;
                esac
            fi
        done < <(git status --porcelain)
        
        echo ""
        echo "## 详细变更内容"
        echo ""
        
        # 生成每个允许文件的 diff
        for file in "${allowed_files[@]}"; do
            if [ -f "$file" ] || [ -d "$file" ]; then
                echo "### $file"
                echo ""
                echo '```diff'
                git diff --no-color -- "$file" 2>/dev/null || echo "(新文件，无 diff)"
                echo '```'
                echo ""
            fi
        done
        
        echo ""
        echo "---"
        echo "请 AI 基于以上变更，生成一个清晰、人性化的 commit message。"
        echo "要求："
        echo "- 用中文"
        echo "- 简洁明了，不超过 50 字符"
        echo "- 体现变更的核心内容"
        echo "- 格式建议：type: description（如：feat: 添加xxx功能, fix: 修复xxx问题, docs: 更新文档, refactor: 重构代码）"
    } > "$DIFF_SUMMARY"
    
    log "INFO" "变更摘要已生成: $DIFF_SUMMARY"
    echo ""
    echo "========================================"
    echo "变更摘要已生成！"
    echo "文件位置: $DIFF_SUMMARY"
    echo ""
    echo "请 AI 读取此文件，分析变更并生成 commit message。"
    echo "生成后，运行 todo-push-commit.sh '<commit-message>' 来提交。"
    echo "========================================"
    echo ""
}

# 同步 OpenClaw 记忆文件到 .openclaw-memory/ 目录
# ⚠️ 注意：现在本地的记忆文件已经是软链接，指向仓库中的 .openclaw-memory/ 目录
# ⚠️ 所以不需要再次同步，跳过这个步骤
sync_openclaw_memory() {
    log "INFO" "步骤 0/3: 同步 OpenClaw 记忆文件（跳过）"
    log "INFO" "  本地记忆文件已设为软链接，指向仓库中的 .openclaw-memory/ 目录"
    log "INFO" "  跳过同步步骤"
}

# 主函数
main() {
    log "INFO" "========================================"
    log "INFO" "Todo Push 脚本开始执行"
    log "INFO" "========================================"
    
    cd "$REPO_ROOT" || error_exit "无法进入仓库目录"
    
    # 0. 同步 OpenClaw 记忆文件
    sync_openclaw_memory
    
    # 1. 获取所有更改
    log "INFO" "步骤 1/3: 检查更改"
    local all_changes=$(git status --porcelain)
    if [ -z "$all_changes" ]; then
        log "INFO" "没有需要提交的更改"
        exit 0
    fi
    
    # 显示所有更改
    log "INFO" "检测到以下更改："
    echo "$all_changes" | while IFS= read -r line; do
        log "INFO" "  $line"
    done
    
    # 2. 过滤允许的文件
    log "INFO" "步骤 2/3: 过滤允许的文件（仅 Notes/、.trae/、创作/）"
    local allowed_files=()
    
    # 使用 git status --porcelain 的输出来获取文件名，这样更可靠
    # 解析 git status --porcelain 的输出，提取文件名
    while IFS= read -r line; do
        if [ -n "$line" ]; then
            # 提取文件名（跳过前面的状态码和空格）
            # git status --porcelain 的输出格式："XY 文件名"，其中 XY 是状态码（2个字符）
            # 用更可靠的方式：跳过前面的状态码和空格
            local file=$(echo "$line" | awk '{print substr($0, 4)}')
            if [ -n "$file" ]; then
                if is_file_allowed "$file"; then
                    allowed_files+=("$file")
                    log "INFO" "  ✓ $file"
                else
                    log "WARN" "  [跳过] $file"
                fi
            fi
        fi
    done < <(git status --porcelain)
    
    # 去重
    local unique_allowed_files=()
    for file in "${allowed_files[@]}"; do
        local found=0
        for unique_file in "${unique_allowed_files[@]}"; do
            if [ "$file" == "$unique_file" ]; then
                found=1
                break
            fi
        done
        if [ $found -eq 0 ]; then
            unique_allowed_files+=("$file")
        fi
    done
    allowed_files=("${unique_allowed_files[@]}")
    
    if [ ${#allowed_files[@]} -eq 0 ]; then
        log "INFO" "没有允许提交的文件，退出"
        exit 0
    fi
    
    # 3. 生成变更摘要
    log "INFO" "步骤 3/3: 生成变更摘要"
    generate_diff_summary "${allowed_files[@]}"
}

# 运行主函数
main
