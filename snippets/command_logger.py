#!/usr/bin/env python3
"""
Command Logger - 记录关键命令行调用
在执行关键命令时，自动记录到日志文件中
"""

import os
import sys
import subprocess
from pathlib import Path
from datetime import datetime
from typing import List, Optional, Dict, Any

# 配置路径
REPO_ROOT = Path(__file__).parent.parent.parent
LOGS_DIR = REPO_ROOT / ".trae" / "logs"
LOGS_DIR.mkdir(parents=True, exist_ok=True)

# 今日命令日志文件
TODAY = datetime.now().strftime("%Y-%m-%d")
COMMAND_LOG_FILE = LOGS_DIR / f"commands_{TODAY}.jsonl"

class CommandLogger:
    """命令记录器"""
    
    def __init__(self):
        self.log_file = COMMAND_LOG_FILE
    
    def log_command(
        self,
        command: List[str],
        cwd: Optional[str] = None,
        success: bool = True,
        output: Optional[str] = None,
        error: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        记录命令执行
        
        Args:
            command: 命令列表（如 ['git', 'status']）
            cwd: 工作目录
            success: 是否成功
            output: 标准输出
            error: 错误输出
            metadata: 额外的元数据
        
        Returns:
            记录的日志条目
        """
        log_entry = {
            "timestamp": datetime.now().isoformat(),
            "command": command,
            "command_str": " ".join(command),
            "cwd": cwd or str(Path.cwd()),
            "success": success,
            "output": output[:2000] if output else None,  # 截断过长的输出
            "error": error[:2000] if error else None,
            "metadata": metadata or {}
        }
        
        # 写入日志文件
        try:
            import json
            with open(self.log_file, 'a', encoding='utf-8') as f:
                f.write(json.dumps(log_entry, ensure_ascii=False))
                f.write('\n')
        except Exception as e:
            print(f"⚠️ 写入命令日志失败: {e}", file=sys.stderr)
        
        return log_entry
    
    def run_and_log(
        self,
        command: List[str],
        cwd: Optional[str] = None,
        capture_output: bool = True,
        metadata: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        运行命令并记录
        
        Args:
            command: 命令列表
            cwd: 工作目录
            capture_output: 是否捕获输出
            metadata: 额外的元数据
        
        Returns:
            包含执行结果的字典
        """
        result = {
            "success": False,
            "returncode": -1,
            "stdout": "",
            "stderr": ""
        }
        
        try:
            if capture_output:
                proc = subprocess.run(
                    command,
                    cwd=cwd,
                    capture_output=True,
                    text=True,
                    timeout=300  # 5分钟超时
                )
                result["returncode"] = proc.returncode
                result["stdout"] = proc.stdout
                result["stderr"] = proc.stderr
                result["success"] = proc.returncode == 0
            else:
                proc = subprocess.run(
                    command,
                    cwd=cwd,
                    timeout=300
                )
                result["returncode"] = proc.returncode
                result["success"] = proc.returncode == 0
        except subprocess.TimeoutExpired:
            result["stderr"] = "Command timed out"
        except Exception as e:
            result["stderr"] = str(e)
        
        # 记录命令
        self.log_command(
            command=command,
            cwd=cwd,
            success=result["success"],
            output=result.get("stdout"),
            error=result.get("stderr"),
            metadata=metadata
        )
        
        return result

# 全局命令记录器实例
_command_logger = None

def get_command_logger() -> CommandLogger:
    """获取全局命令记录器"""
    global _command_logger
    if _command_logger is None:
        _command_logger = CommandLogger()
    return _command_logger

def log_command(
    command: List[str],
    cwd: Optional[str] = None,
    success: bool = True,
    output: Optional[str] = None,
    error: Optional[str] = None,
    metadata: Optional[Dict[str, Any]] = None
) -> Dict[str, Any]:
    """记录命令执行（便捷函数）"""
    logger = get_command_logger()
    return logger.log_command(
        command=command,
        cwd=cwd,
        success=success,
        output=output,
        error=error,
        metadata=metadata
    )

def run_and_log(
    command: List[str],
    cwd: Optional[str] = None,
    capture_output: bool = True,
    metadata: Optional[Dict[str, Any]] = None
) -> Dict[str, Any]:
    """运行命令并记录（便捷函数）"""
    logger = get_command_logger()
    return logger.run_and_log(
        command=command,
        cwd=cwd,
        capture_output=capture_output,
        metadata=metadata
    )

def get_recent_commands(limit: int = 10) -> List[Dict[str, Any]]:
    """获取最近的命令记录"""
    logger = get_command_logger()
    commands = []
    
    if logger.log_file.exists():
        try:
            import json
            with open(logger.log_file, 'r', encoding='utf-8') as f:
                for line in f:
                    line = line.strip()
                    if line:
                        commands.append(json.loads(line))
        except Exception as e:
            print(f"⚠️ 读取命令日志失败: {e}", file=sys.stderr)
    
    # 返回最近的 limit 条
    return commands[-limit:] if commands else []

if __name__ == "__main__":
    # 测试命令记录器
    print("=" * 60)
    print("Command Logger 测试")
    print("=" * 60)
    
    # 测试1: 记录一个简单的命令
    print("\n1. 测试记录命令...")
    log_command(
        command=["echo", "Hello, Command Logger!"],
        success=True,
        output="Hello, Command Logger!",
        metadata={"test": "simple"}
    )
    print("✅ 命令已记录")
    
    # 测试2: 运行并记录 git status
    print("\n2. 测试运行并记录 git status...")
    result = run_and_log(
        command=["git", "status"],
        cwd=str(REPO_ROOT),
        metadata={"purpose": "check git status"}
    )
    print(f"✅ git status 已记录，成功: {result['success']}")
    
    # 测试3: 查看最近的命令
    print("\n3. 查看最近的命令记录...")
    recent_commands = get_recent_commands(limit=5)
    print(f"✅ 找到 {len(recent_commands)} 条命令记录")
    for i, cmd in enumerate(recent_commands, 1):
        print(f"   {i}. {cmd['command_str']}")
    
    print("\n" + "=" * 60)
    print(f"✅ 测试完成！日志文件: {COMMAND_LOG_FILE}")
    print("=" * 60)
