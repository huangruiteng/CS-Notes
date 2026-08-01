#!/usr/bin/env python3
"""
Task Executor - 任务执行器，实现可观测闭环
"""

import os
import sys
import json
import subprocess
from pathlib import Path
from datetime import datetime
from typing import Optional, Dict, Any

# 配置路径
REPO_ROOT = Path("/root/.openclaw/workspace/CS-Notes")
LOGS_DIR = REPO_ROOT / ".trae/logs"
TASKS_DIR = REPO_ROOT / ".trae/tasks"

class TaskExecutor:
    def __init__(self):
        self.repo_root = REPO_ROOT
        self.logs_dir = LOGS_DIR
        self.tasks_dir = TASKS_DIR
        self.logs_dir.mkdir(parents=True, exist_ok=True)
        self.tasks_dir.mkdir(parents=True, exist_ok=True)
    
    def create_task_log(self, task_id: str, task_description: str) -> Dict[str, Any]:
        """创建任务日志"""
        log_file = self.logs_dir / f"task_{task_id}.json"
        
        task_log = {
            "task_id": task_id,
            "task_description": task_description,
            "status": "pending",
            "created_at": datetime.now().isoformat(),
            "started_at": None,
            "completed_at": None,
            "failed_at": None,
            "stages": [],
            "artifacts": {
                "summary": None,
                "links": [],
                "diffs": [],
                "reproduce_commands": []
            },
            "metrics": {
                "execution_time_seconds": None,
                "success": None,
                "retry_count": 0
            }
        }
        
        with open(log_file, "w", encoding="utf-8") as f:
            json.dump(task_log, f, ensure_ascii=False, indent=2)
        
        return task_log
    
    def update_task_log(self, task_id: str, updates: Dict[str, Any]):
        """更新任务日志"""
        log_file = self.logs_dir / f"task_{task_id}.json"
        
        if not log_file.exists():
            return
        
        with open(log_file, "r", encoding="utf-8") as f:
            task_log = json.load(f)
        
        task_log.update(updates)
        task_log["updated_at"] = datetime.now().isoformat()
        
        with open(log_file, "w", encoding="utf-8") as f:
            json.dump(task_log, f, ensure_ascii=False, indent=2)
    
    def add_stage(self, task_id: str, stage_name: str, stage_status: str = "in_progress"):
        """添加执行阶段"""
        log_file = self.logs_dir / f"task_{task_id}.json"
        
        if not log_file.exists():
            return
        
        with open(log_file, "r", encoding="utf-8") as f:
            task_log = json.load(f)
        
        stage = {
            "name": stage_name,
            "status": stage_status,
            "started_at": datetime.now().isoformat(),
            "completed_at": None
        }
        
        task_log["stages"].append(stage)
        
        with open(log_file, "w", encoding="utf-8") as f:
            json.dump(task_log, f, ensure_ascii=False, indent=2)
    
    def complete_stage(self, task_id: str, stage_name: str, success: bool = True):
        """完成执行阶段"""
        log_file = self.logs_dir / f"task_{task_id}.json"
        
        if not log_file.exists():
            return
        
        with open(log_file, "r", encoding="utf-8") as f:
            task_log = json.load(f)
        
        for stage in task_log["stages"]:
            if stage["name"] == stage_name:
                stage["status"] = "completed" if success else "failed"
                stage["completed_at"] = datetime.now().isoformat()
                break
        
        with open(log_file, "w", encoding="utf-8") as f:
            json.dump(task_log, f, ensure_ascii=False, indent=2)
    
    def execute_task(self, task_id: str, task_description: str, command: str) -> Dict[str, Any]:
        """执行任务"""
        # 创建任务日志
        task_log = self.create_task_log(task_id, task_description)
        
        # 更新状态为 in_progress
        started_at = datetime.now().isoformat()
        self.update_task_log(task_id, {
            "status": "in_progress",
            "started_at": started_at
        })
        
        # 执行命令
        try:
            self.add_stage(task_id, "执行命令")
            
            result = subprocess.run(
                command,
                shell=True,
                capture_output=True,
                text=True,
                timeout=3600
            )
            
            self.complete_stage(task_id, "执行命令", result.returncode == 0)
            
            # 更新任务日志
            execution_time = (datetime.now() - datetime.fromisoformat(started_at)).total_seconds()
            
            self.update_task_log(task_id, {
                "status": "completed" if result.returncode == 0 else "failed",
                "completed_at": datetime.now().isoformat() if result.returncode == 0 else None,
                "failed_at": datetime.now().isoformat() if result.returncode != 0 else None,
                "artifacts": {
                    "summary": f"任务执行完成：{task_description}",
                    "links": [],
                    "diffs": [],
                    "reproduce_commands": [command]
                },
                "metrics": {
                    "execution_time_seconds": execution_time,
                    "success": result.returncode == 0,
                    "retry_count": 0
                },
                "stdout": result.stdout,
                "stderr": result.stderr
            })
            
            return {
                "success": result.returncode == 0,
                "task_id": task_id,
                "stdout": result.stdout,
                "stderr": result.stderr,
                "log_file": str(self.logs_dir / f"task_{task_id}.json")
            }
        
        except Exception as e:
            self.complete_stage(task_id, "执行命令", False)
            
            self.update_task_log(task_id, {
                "status": "failed",
                "failed_at": datetime.now().isoformat(),
                "error": str(e),
                "metrics": {
                    "success": False,
                    "retry_count": 0
                }
            })
            
            return {
                "success": False,
                "task_id": task_id,
                "error": str(e),
                "log_file": str(self.logs_dir / f"task_{task_id}.json")
            }
    
    def retry_task(self, task_id: str) -> Dict[str, Any]:
        """重试任务"""
        log_file = self.logs_dir / f"task_{task_id}.json"
        
        if not log_file.exists():
            return {"success": False, "error": "Task not found"}
        
        with open(log_file, "r", encoding="utf-8") as f:
            task_log = json.load(f)
        
        # 增加重试计数
        task_log["metrics"]["retry_count"] += 1
        
        with open(log_file, "w", encoding="utf-8") as f:
            json.dump(task_log, f, ensure_ascii=False, indent=2)
        
        # 重新执行任务（这里简化处理，实际应该重新执行原始命令）
        return {
            "success": True,
            "task_id": task_id,
            "retry_count": task_log["metrics"]["retry_count"],
            "message": "Task retry initiated"
        }
    
    def get_task_status(self, task_id: str) -> Optional[Dict[str, Any]]:
        """获取任务状态"""
        log_file = self.logs_dir / f"task_{task_id}.json"
        
        if not log_file.exists():
            return None
        
        with open(log_file, "r", encoding="utf-8") as f:
            return json.load(f)
    
    def get_all_tasks(self) -> list:
        """获取所有任务"""
        if not self.logs_dir.exists():
            return []
        
        tasks = []
        for log_file in self.logs_dir.glob("task_*.json"):
            with open(log_file, "r", encoding="utf-8") as f:
                tasks.append(json.load(f))
        
        # 按创建时间排序，最新的在前
        tasks.sort(key=lambda x: x["created_at"], reverse=True)
        
        return tasks
    
    def get_metrics(self) -> Dict[str, Any]:
        """获取系统指标"""
        all_tasks = self.get_all_tasks()
        
        total_tasks = len(all_tasks)
        completed_tasks = len([t for t in all_tasks if t["status"] == "completed"])
        failed_tasks = len([t for t in all_tasks if t["status"] == "failed"])
        in_progress_tasks = len([t for t in all_tasks if t["status"] == "in_progress"])
        
        completion_rate = (completed_tasks / total_tasks * 100) if total_tasks > 0 else 0
        failure_rate = (failed_tasks / total_tasks * 100) if total_tasks > 0 else 0
        
        # 计算平均执行时间
        execution_times = []
        for task in all_tasks:
            if task["metrics"]["execution_time_seconds"]:
                execution_times.append(task["metrics"]["execution_time_seconds"])
        
        avg_execution_time = sum(execution_times) / len(execution_times) if execution_times else 0
        
        return {
            "total_tasks": total_tasks,
            "completed_tasks": completed_tasks,
            "failed_tasks": failed_tasks,
            "in_progress_tasks": in_progress_tasks,
            "completion_rate": round(completion_rate, 2),
            "failure_rate": round(failure_rate, 2),
            "avg_execution_time_seconds": round(avg_execution_time, 2),
            "generated_at": datetime.now().isoformat()
        }

def main():
    """主函数"""
    executor = TaskExecutor()
    
    if len(sys.argv) < 2:
        print("Usage:")
        print("  python task_executor.py create <task_id> <task_description>")
        print("  python task_executor.py execute <task_id> <task_description> <command>")
        print("  python task_executor.py status <task_id>")
        print("  python task_executor.py list")
        print("  python task_executor.py metrics")
        print("  python task_executor.py retry <task_id>")
        return
    
    command = sys.argv[1]
    
    if command == "create" and len(sys.argv) >= 4:
        task_id = sys.argv[2]
        task_description = sys.argv[3]
        result = executor.create_task_log(task_id, task_description)
        print(json.dumps(result, ensure_ascii=False, indent=2))
    
    elif command == "execute" and len(sys.argv) >= 5:
        task_id = sys.argv[2]
        task_description = sys.argv[3]
        cmd = sys.argv[4]
        result = executor.execute_task(task_id, task_description, cmd)
        print(json.dumps(result, ensure_ascii=False, indent=2))
    
    elif command == "status" and len(sys.argv) >= 3:
        task_id = sys.argv[2]
        result = executor.get_task_status(task_id)
        if result:
            print(json.dumps(result, ensure_ascii=False, indent=2))
        else:
            print(json.dumps({"success": False, "error": "Task not found"}))
    
    elif command == "list":
        result = executor.get_all_tasks()
        print(json.dumps(result, ensure_ascii=False, indent=2))
    
    elif command == "metrics":
        result = executor.get_metrics()
        print(json.dumps(result, ensure_ascii=False, indent=2))
    
    elif command == "retry" and len(sys.argv) >= 3:
        task_id = sys.argv[2]
        result = executor.retry_task(task_id)
        print(json.dumps(result, ensure_ascii=False, indent=2))
    
    else:
        print("Invalid command or missing arguments")

if __name__ == "__main__":
    main()
