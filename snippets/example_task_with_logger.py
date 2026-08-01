#!/usr/bin/env python3
"""
示例任务 - 展示如何使用 task_execution_logger.py
让 task_execution_logger.py 真正用起来！
"""

import sys
from pathlib import Path

# 添加父目录到 sys.path，以便导入 task_execution_logger
sys.path.insert(0, str(Path(__file__).parent))

from task_execution_logger import (
    TaskExecutionLogger,
    TaskStage,
    LogLevel,
    task_context,
    create_logger
)


def example_task():
    """示例任务 - 展示如何使用 task_execution_logger.py"""
    
    task_id = "example-task-20260219-001"
    logger = create_logger()
    
    print("=" * 60)
    print("🎯 示例任务 - 使用 task_execution_logger.py")
    print("=" * 60)
    print()
    
    # 使用任务执行上下文管理器
    with task_context(task_id) as ctx:
        # 记录计划阶段
        logger.log_info(task_id, TaskStage.PLANNING, "开始计划任务")
        logger.log_debug(task_id, TaskStage.PLANNING, "分析任务需求")
        logger.log_debug(task_id, TaskStage.PLANNING, "定义验收标准")
        
        # 记录执行阶段
        logger.log_info(task_id, TaskStage.EXECUTING, "开始执行任务")
        logger.log_info(task_id, TaskStage.EXECUTING, "执行步骤 1/3")
        logger.log_info(task_id, TaskStage.EXECUTING, "执行步骤 2/3")
        logger.log_info(task_id, TaskStage.EXECUTING, "执行步骤 3/3")
        
        # 记录验证阶段
        logger.log_info(task_id, TaskStage.VERIFYING, "验证执行结果")
        
        # 保存任务产物
        from task_execution_logger import TaskArtifact
        artifact = TaskArtifact(
            task_id=task_id,
            execution_summary="示例任务执行成功，展示了如何使用 task_execution_logger.py",
            product_links=["https://github.com/huangrt01/CS-Notes"],
            key_diffs=["modified: snippets/example_task_with_logger.py"],
            reproduction_commands=["python3 snippets/example_task_with_logger.py"]
        )
        logger.save_artifact(artifact)
    
    print()
    print("=" * 60)
    print("✅ 示例任务完成！")
    print("=" * 60)
    print()
    
    # 显示指标
    print("📊 整体指标:")
    metrics = logger.get_overall_metrics()
    for key, value in metrics.items():
        print(f"  {key}: {value}")
    print()
    
    # 检查告警
    print("🚨 告警检查:")
    alerts = logger.check_alerts()
    if alerts:
        for alert in alerts:
            print(f"  {alert}")
    else:
        print("  无告警")
    print()
    
    print("=" * 60)


def main():
    """主函数"""
    example_task()


if __name__ == "__main__":
    main()
