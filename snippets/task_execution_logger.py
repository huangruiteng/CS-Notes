#!/usr/bin/env python3
"""
任务执行可观测闭环 - 日志系统
提供结构化日志输出、任务状态机、重试队列、指标收集等功能
"""

import os
import sys
import json
import time
from pathlib import Path
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, asdict, field
from enum import Enum


# ============================================
# 枚举定义
# ============================================

class LogLevel(Enum):
    """日志级别"""
    DEBUG = "DEBUG"
    INFO = "INFO"
    WARN = "WARN"
    ERROR = "ERROR"
    SUCCESS = "SUCCESS"


class TaskStage(Enum):
    """任务执行阶段"""
    PENDING = "pending"
    PLANNING = "planning"
    EXECUTING = "executing"
    VERIFYING = "verifying"
    COMPLETED = "completed"
    FAILED = "failed"


class TaskStatus(Enum):
    """任务状态"""
    PENDING = "pending"
    IN_PROGRESS = "in-progress"
    COMPLETED = "completed"
    FAILED = "failed"
    RETRYING = "retrying"
    NEEDS_ATTENTION = "needs-attention"


# ============================================
# 数据类
# ============================================

@dataclass
class LogEntry:
    """日志条目"""
    task_id: str
    timestamp: str
    level: str
    stage: str
    message: str
    agent: str = "unknown"
    details: Dict[str, Any] = field(default_factory=dict)


@dataclass
class TaskMetrics:
    """任务指标"""
    task_id: str
    agent: str = "unknown"
    started_at: Optional[str] = None
    completed_at: Optional[str] = None
    execution_time_seconds: float = 0.0
    retry_count: int = 0
    status: str = "pending"


@dataclass
class TaskArtifact:
    """任务产物"""
    task_id: str
    execution_summary: str = ""
    product_links: List[str] = field(default_factory=list)
    key_diffs: List[str] = field(default_factory=list)
    reproduction_commands: List[str] = field(default_factory=list)


# ============================================
# 任务执行日志系统
# ============================================

class TaskExecutionLogger:
    """任务执行日志系统"""
    
    def __init__(self, repo_root: Optional[Path] = None):
        """初始化日志系统"""
        if repo_root is None:
            repo_root = Path(__file__).parent.parent.parent
        
        self.repo_root = repo_root
        self.logs_dir = repo_root / ".trae" / "logs"
        self.logs_dir.mkdir(parents=True, exist_ok=True)
        
        # 今天的日志文件
        today = datetime.now().strftime("%Y%m%d")
        self.log_file = self.logs_dir / f"task_execution_{today}.jsonl"
        
        # 指标文件
        self.metrics_file = self.logs_dir / "task_metrics.json"
        
        # 产物目录
        self.artifacts_dir = self.logs_dir / "artifacts"
        self.artifacts_dir.mkdir(parents=True, exist_ok=True)
        
        # 重试队列文件
        self.retry_queue_file = self.logs_dir / "retry_queue.json"
        
        # 内存中的指标缓存
        self.metrics: Dict[str, TaskMetrics] = {}
        self._load_metrics()
    
    def _log(self, entry: LogEntry):
        """写入日志"""
        log_line = json.dumps(asdict(entry), ensure_ascii=False)
        with open(self.log_file, "a", encoding="utf-8") as f:
            f.write(log_line + "\n")
    
    def log(self, task_id: str, level: LogLevel, stage: TaskStage, 
            message: str, details: Optional[Dict[str, Any]] = None,
            agent: str = "unknown"):
        """记录日志"""
        entry = LogEntry(
            task_id=task_id,
            timestamp=datetime.now().isoformat(),
            level=level.value,
            stage=stage.value,
            message=message,
            agent=agent,
            details=details or {}
        )
        self._log(entry)
    
    def log_debug(self, task_id: str, stage: TaskStage, message: str, 
                  details: Optional[Dict[str, Any]] = None,
                  agent: str = "unknown"):
        """记录调试日志"""
        self.log(task_id, LogLevel.DEBUG, stage, message, details, agent)
    
    def log_info(self, task_id: str, stage: TaskStage, message: str, 
                 details: Optional[Dict[str, Any]] = None,
                 agent: str = "unknown"):
        """记录信息日志"""
        self.log(task_id, LogLevel.INFO, stage, message, details, agent)
    
    def log_warn(self, task_id: str, stage: TaskStage, message: str, 
                 details: Optional[Dict[str, Any]] = None,
                 agent: str = "unknown"):
        """记录警告日志"""
        self.log(task_id, LogLevel.WARN, stage, message, details, agent)
    
    def log_error(self, task_id: str, stage: TaskStage, message: str, 
                  details: Optional[Dict[str, Any]] = None,
                  agent: str = "unknown"):
        """记录错误日志"""
        self.log(task_id, LogLevel.ERROR, stage, message, details, agent)
    
    def log_success(self, task_id: str, stage: TaskStage, message: str, 
                   details: Optional[Dict[str, Any]] = None,
                   agent: str = "unknown"):
        """记录成功日志"""
        self.log(task_id, LogLevel.SUCCESS, stage, message, details, agent)
    
    # ============================================
    # 任务指标管理
    # ============================================
    
    def _load_metrics(self):
        """加载指标"""
        if self.metrics_file.exists():
            try:
                with open(self.metrics_file, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    for task_id, metrics_data in data.items():
                        self.metrics[task_id] = TaskMetrics(**metrics_data)
            except Exception as e:
                print(f"Error loading metrics: {e}", file=sys.stderr)
    
    def _save_metrics(self):
        """保存指标"""
        data = {task_id: asdict(metrics) for task_id, metrics in self.metrics.items()}
        with open(self.metrics_file, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
    
    def start_task(self, task_id: str, agent: str = "unknown"):
        """开始任务"""
        if task_id not in self.metrics:
            self.metrics[task_id] = TaskMetrics(task_id=task_id, agent=agent)
        else:
            self.metrics[task_id].agent = agent
        
        metrics = self.metrics[task_id]
        metrics.started_at = datetime.now().isoformat()
        metrics.status = TaskStatus.IN_PROGRESS.value
        self._save_metrics()
        
        self.log_info(task_id, TaskStage.PLANNING, "任务开始执行", agent=agent)
    
    def complete_task(self, task_id: str, agent: str = "unknown"):
        """完成任务"""
        if task_id in self.metrics:
            metrics = self.metrics[task_id]
            metrics.agent = agent
            metrics.completed_at = datetime.now().isoformat()
            metrics.status = TaskStatus.COMPLETED.value
            
            if metrics.started_at:
                started = datetime.fromisoformat(metrics.started_at)
                completed = datetime.fromisoformat(metrics.completed_at)
                metrics.execution_time_seconds = (completed - started).total_seconds()
            
            self._save_metrics()
        
        self.log_success(task_id, TaskStage.COMPLETED, "任务完成", agent=agent)
    
    def fail_task(self, task_id: str, error_message: str):
        """任务失败"""
        if task_id in self.metrics:
            metrics = self.metrics[task_id]
            metrics.status = TaskStatus.FAILED.value
            self._save_metrics()
        
        self.log_error(task_id, TaskStage.FAILED, f"任务失败: {error_message}")
    
    def retry_task(self, task_id: str, retry_count: int):
        """重试任务"""
        if task_id in self.metrics:
            metrics = self.metrics[task_id]
            metrics.retry_count = retry_count
            metrics.status = TaskStatus.RETRYING.value
            self._save_metrics()
        
        self.log_info(task_id, TaskStage.EXECUTING, f"任务重试 (第 {retry_count} 次)")
    
    # ============================================
    # 重试队列管理
    # ============================================
    
    def _load_retry_queue(self) -> List[Dict[str, Any]]:
        """加载重试队列"""
        if self.retry_queue_file.exists():
            try:
                with open(self.retry_queue_file, "r", encoding="utf-8") as f:
                    return json.load(f)
            except Exception as e:
                print(f"Error loading retry queue: {e}", file=sys.stderr)
        return []
    
    def _save_retry_queue(self, queue: List[Dict[str, Any]]):
        """保存重试队列"""
        with open(self.retry_queue_file, "w", encoding="utf-8") as f:
            json.dump(queue, f, ensure_ascii=False, indent=2)
    
    def add_to_retry_queue(self, task_id: str, retry_after_seconds: int = 0):
        """添加到重试队列"""
        queue = self._load_retry_queue()
        
        # 检查是否已在队列中
        for item in queue:
            if item["task_id"] == task_id:
                return
        
        retry_at = (datetime.now() + timedelta(seconds=retry_after_seconds)).isoformat()
        queue.append({
            "task_id": task_id,
            "retry_at": retry_at,
            "retry_count": 0,
            "added_at": datetime.now().isoformat()
        })
        
        self._save_retry_queue(queue)
        self.log_info(task_id, TaskStage.EXECUTING, f"任务已添加到重试队列，将在 {retry_after_seconds} 秒后重试")
    
    def get_ready_retry_tasks(self) -> List[str]:
        """获取可以重试的任务"""
        queue = self._load_retry_queue()
        now = datetime.now()
        ready_tasks = []
        
        for item in queue:
            retry_at = datetime.fromisoformat(item["retry_at"])
            if retry_at <= now:
                ready_tasks.append(item["task_id"])
        
        return ready_tasks
    
    def remove_from_retry_queue(self, task_id: str):
        """从重试队列中移除"""
        queue = self._load_retry_queue()
        queue = [item for item in queue if item["task_id"] != task_id]
        self._save_retry_queue(queue)
    
    # ============================================
    # 任务产物管理
    # ============================================
    
    def save_artifact(self, artifact: TaskArtifact):
        """保存任务产物"""
        artifact_file = self.artifacts_dir / f"{artifact.task_id}.json"
        with open(artifact_file, "w", encoding="utf-8") as f:
            json.dump(asdict(artifact), f, ensure_ascii=False, indent=2)
    
    def load_artifact(self, task_id: str) -> Optional[TaskArtifact]:
        """加载任务产物"""
        artifact_file = self.artifacts_dir / f"{task_id}.json"
        if artifact_file.exists():
            with open(artifact_file, "r", encoding="utf-8") as f:
                data = json.load(f)
                return TaskArtifact(**data)
        return None
    
    # ============================================
    # 指标统计
    # ============================================
    
    def get_overall_metrics(self) -> Dict[str, Any]:
        """获取整体指标"""
        total_tasks = len(self.metrics)
        completed_tasks = sum(1 for m in self.metrics.values() 
                            if m.status == TaskStatus.COMPLETED.value)
        failed_tasks = sum(1 for m in self.metrics.values() 
                         if m.status == TaskStatus.FAILED.value)
        retrying_tasks = sum(1 for m in self.metrics.values() 
                           if m.status == TaskStatus.RETRYING.value)
        
        # 计算平均执行时间
        execution_times = [m.execution_time_seconds for m in self.metrics.values() 
                         if m.execution_time_seconds > 0]
        avg_execution_time = sum(execution_times) / len(execution_times) if execution_times else 0
        
        # 计算完成率和失败率
        completion_rate = (completed_tasks / total_tasks * 100) if total_tasks > 0 else 0
        failure_rate = (failed_tasks / total_tasks * 100) if total_tasks > 0 else 0
        
        # 重试率
        retry_count = sum(m.retry_count for m in self.metrics.values())
        retry_rate = (retry_count / total_tasks * 100) if total_tasks > 0 else 0
        
        # 按 Agent 分组统计
        agent_metrics = {}
        for task_id, metrics in self.metrics.items():
            agent = metrics.agent or 'unknown'
            if agent not in agent_metrics:
                agent_metrics[agent] = {
                    'total_tasks': 0,
                    'completed_tasks': 0,
                    'failed_tasks': 0,
                    'execution_times': []
                }
            
            agent_metrics[agent]['total_tasks'] += 1
            if metrics.status == TaskStatus.COMPLETED.value:
                agent_metrics[agent]['completed_tasks'] += 1
            if metrics.status == TaskStatus.FAILED.value:
                agent_metrics[agent]['failed_tasks'] += 1
            if metrics.execution_time_seconds > 0:
                agent_metrics[agent]['execution_times'].append(metrics.execution_time_seconds)
        
        # 计算每个 agent 的详细指标
        for agent in agent_metrics:
            am = agent_metrics[agent]
            am['completion_rate'] = round((am['completed_tasks'] / am['total_tasks'] * 100) if am['total_tasks'] > 0 else 0, 2)
            am['avg_execution_time_seconds'] = round((sum(am['execution_times']) / len(am['execution_times']) if am['execution_times'] else 0), 2)
            am['avg_execution_time_minutes'] = round(am['avg_execution_time_seconds'] / 60, 2)
        
        return {
            "total_tasks": total_tasks,
            "completed_tasks": completed_tasks,
            "failed_tasks": failed_tasks,
            "retrying_tasks": retrying_tasks,
            "completion_rate": round(completion_rate, 2),
            "failure_rate": round(failure_rate, 2),
            "retry_rate": round(retry_rate, 2),
            "avg_execution_time_seconds": round(avg_execution_time, 2),
            "avg_execution_time_minutes": round(avg_execution_time / 60, 2),
            "agent_metrics": agent_metrics
        }
    
    # ============================================
    # 告警检查
    # ============================================
    
    def check_alerts(self, completion_rate_threshold: float = 80.0, 
                    failure_rate_threshold: float = 20.0,
                    avg_execution_time_threshold_minutes: float = 30.0) -> List[str]:
        """检查告警"""
        alerts = []
        metrics = self.get_overall_metrics()
        
        if metrics["completion_rate"] < completion_rate_threshold:
            alerts.append(f"⚠️ 任务完成率过低: {metrics['completion_rate']}% (阈值: {completion_rate_threshold}%)")
        
        if metrics["failure_rate"] > failure_rate_threshold:
            alerts.append(f"⚠️ 任务失败率过高: {metrics['failure_rate']}% (阈值: {failure_rate_threshold}%)")
        
        if metrics["avg_execution_time_minutes"] > avg_execution_time_threshold_minutes:
            alerts.append(f"⚠️ 平均执行时间过长: {metrics['avg_execution_time_minutes']} 分钟 (阈值: {avg_execution_time_threshold_minutes} 分钟)")
        
        return alerts


# ============================================
# 上下文管理器
# ============================================

class TaskExecutionContext:
    """任务执行上下文管理器"""
    
    def __init__(self, logger: TaskExecutionLogger, task_id: str):
        self.logger = logger
        self.task_id = task_id
        self.start_time = None
    
    def __enter__(self):
        self.start_time = time.time()
        self.logger.start_task(self.task_id)
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        if exc_type is not None:
            # 发生异常
            error_message = f"{exc_type.__name__}: {exc_val}"
            self.logger.fail_task(self.task_id, error_message)
            return False  # 重新抛出异常
        else:
            # 正常完成
            self.logger.complete_task(self.task_id)
            return True


# ============================================
# 便捷函数
# ============================================

def create_logger(repo_root: Optional[Path] = None) -> TaskExecutionLogger:
    """创建日志系统实例"""
    return TaskExecutionLogger(repo_root)


def task_context(task_id: str, repo_root: Optional[Path] = None) -> TaskExecutionContext:
    """创建任务执行上下文"""
    logger = create_logger(repo_root)
    return TaskExecutionContext(logger, task_id)


# ============================================
# 主函数（测试用）
# ============================================

if __name__ == "__main__":
    print("=" * 60)
    print("任务执行可观测闭环 - 日志系统")
    print("=" * 60)
    
    # 创建日志系统
    logger = create_logger()
    print(f"日志文件: {logger.log_file}")
    print(f"指标文件: {logger.metrics_file}")
    print()
    
    # 测试任务执行
    test_task_id = "test-task-001"
    
    print(f"测试任务: {test_task_id}")
    print()
    
    with task_context(test_task_id) as ctx:
        # 记录一些日志
        logger.log_info(test_task_id, TaskStage.PLANNING, "开始计划任务")
        logger.log_debug(test_task_id, TaskStage.PLANNING, "分析任务需求")
        
        logger.log_info(test_task_id, TaskStage.EXECUTING, "开始执行任务")
        logger.log_info(test_task_id, TaskStage.EXECUTING, "执行步骤 1/3")
        logger.log_info(test_task_id, TaskStage.EXECUTING, "执行步骤 2/3")
        logger.log_info(test_task_id, TaskStage.EXECUTING, "执行步骤 3/3")
        
        logger.log_info(test_task_id, TaskStage.VERIFYING, "验证执行结果")
        
        # 保存任务产物
        artifact = TaskArtifact(
            task_id=test_task_id,
            execution_summary="测试任务执行成功",
            product_links=["https://github.com/example/test"],
            key_diffs=["modified: test.txt"],
            reproduction_commands=["python3 test.py"]
        )
        logger.save_artifact(artifact)
    
    print()
    print("任务执行完成！")
    print()
    
    # 显示指标
    print("整体指标:")
    metrics = logger.get_overall_metrics()
    for key, value in metrics.items():
        print(f"  {key}: {value}")
    print()
    
    # 检查告警
    print("告警检查:")
    alerts = logger.check_alerts()
    if alerts:
        for alert in alerts:
            print(f"  {alert}")
    else:
        print("  无告警")
    print()
    
    print("=" * 60)
    print("测试完成！")
    print("=" * 60)
