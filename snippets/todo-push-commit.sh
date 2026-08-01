#!/bin/bash
# Todo Push Commit 脚本 - 接受 commit message，执行 git add/commit/push
# 严格控制 git add 范围，保护隐私

# 设置 UTF-8 编码，确保能正确处理中文文件名
export LANG=en_US.UTF-8
export LC_ALL=en_US.UTF-8
export LC_CTYPE=en_US.UTF-8

# 配置
REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
LOG_DIR="$REPO_ROOT/.trae/logs"
LOG_FILE="$LOG_DIR/todo-push-commit-$(date +%Y%m%d).log"
DEFAULT_BRANCH="master"

# Git add 白名单：仅允许这些文件夹和文件
ALLOWED_FOLDERS=(
    "Notes/"
    ".trae/"
    "创作/"
    ".openclaw-memory/"
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

# 主函数
main() {
    local commit_msg="$1"
    
    if [ -z "$commit_msg" ]; then
        echo "使用方法: $0 '<commit-message>'"
        echo "示例: $0 'docs: 更新OpenClaw部署教程'"
        exit 1
    fi
    
    log "INFO" "========================================"
    log "INFO" "Todo Push Commit 脚本开始执行"
    log "INFO" "========================================"
    
    cd "$REPO_ROOT" || error_exit "无法进入仓库目录"
    
    # 1. 检查更改
    log "INFO" "步骤 1/4: 检查更改"
    local all_changes=$(git status --porcelain)
    if [ -z "$all_changes" ]; then
        log "INFO" "没有需要提交的更改"
        exit 0
    fi
    
    # 2. 过滤允许的文件
    log "INFO" "步骤 2/4: 过滤允许的文件（仅 Notes/、.trae/、创作/）"
    local allowed_files=()
    
    # 使用更可靠的方式获取文件名（支持中文）
    # 使用 -z 选项来获取 NUL 分隔的文件名，确保能正确处理中文和特殊字符
    # 先获取所有已修改的文件
    while IFS= read -r -d $'\0' file; do
        if [ -n "$file" ]; then
            if is_file_allowed "$file"; then
                allowed_files+=("$file")
                log "INFO" "  ✓ $file"
            else
                log "WARN" "  [跳过] $file"
            fi
        fi
    done < <(git diff --name-only -z)
    
    # 再获取所有未跟踪的文件
    while IFS= read -r -d $'\0' file; do
        if [ -n "$file" ]; then
            if is_file_allowed "$file"; then
                allowed_files+=("$file")
                log "INFO" "  ✓ $file"
            else
                log "WARN" "  [跳过] $file"
            fi
        fi
    done < <(git ls-files --others --exclude-standard -z)
    
    # 去重（兼容旧版本 Bash，不使用关联数组）
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
    
    log "INFO" "允许提交的文件："
    for file in "${allowed_files[@]}"; do
        log "INFO" "  ✓ $file"
    done
    
    # 3. 执行 git add
    log "INFO" "步骤 3/4: 执行 git add（安全模式）"
    for file in "${allowed_files[@]}"; do
        git add "$file" >> "$LOG_FILE" 2>&1
        log "INFO" "  add: $file"
    done
    
    # 4. 执行 commit & push
    log "INFO" "步骤 4/4: 执行 commit & push"
    log "INFO" "Commit message: \"$commit_msg\""
    
    if git commit -m "$commit_msg" >> "$LOG_FILE" 2>&1; then
        log "INFO" "Commit 成功"
    else
        log "ERROR" "Commit 失败，请检查"
        exit 1
    fi
    
    if git push origin "$DEFAULT_BRANCH" >> "$LOG_FILE" 2>&1; then
        log "INFO" "Push 成功！"
        log "INFO" "========================================"
        log "INFO" "推送完成！"
        log "INFO" "========================================"
        
        # 输出 GitHub commit 链接
        local commit_hash=$(git rev-parse HEAD)
        local repo_url=$(git remote get-url origin | sed 's|git@github.com:|https://github.com/|; s|\.git$||')
        local commit_url="${repo_url}/commit/${commit_hash}"
        log "INFO" "GitHub Commit 链接: ${commit_url}"
        echo "GitHub Commit 链接: ${commit_url}"
    else
        log "ERROR" "Push 失败，请检查日志"
        exit 1
    fi
}

# 运行主函数
main "$@"
