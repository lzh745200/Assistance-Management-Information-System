"""
调度任务模块

提供定时任务和调度相关的功能
"""

from typing import Dict, Any, Optional, List, Callable
from datetime import datetime
import logging

logger = logging.getLogger(__name__)


class SchedulerTask:
    """调度任务类"""

    def __init__(
        self,
        name: str,
        func: Callable,
        trigger: str = "interval",
        interval: int = 60,
        args: tuple = None,
        kwargs: dict = None,
    ):
        self.name = name
        self.func = func
        self.trigger = trigger
        self.interval = interval
        self.args = args or ()
        self.kwargs = kwargs or {}
        self.last_run: Optional[datetime] = None
        self.next_run: Optional[datetime] = None
        self.enabled = True

    def run(self):
        """执行任务"""
        if not self.enabled:
            return
        try:
            self.func(*self.args, **self.kwargs)
            self.last_run = datetime.now()
        except Exception as e:
            logger.error(f"任务 {self.name} 执行失败: {e}")


class TaskScheduler:
    """任务调度器"""

    def __init__(self):
        self.tasks: Dict[str, SchedulerTask] = {}
        self._running = False

    def add_task(self, task: SchedulerTask):
        """添加任务"""
        self.tasks[task.name] = task

    def remove_task(self, name: str):
        """移除任务"""
        if name in self.tasks:
            del self.tasks[name]

    def get_task(self, name: str) -> Optional[SchedulerTask]:
        """获取任务"""
        return self.tasks.get(name)

    def list_tasks(self) -> List[Dict[str, Any]]:
        """列出所有任务"""
        return [
            {
                "name": task.name,
                "trigger": task.trigger,
                "interval": task.interval,
                "enabled": task.enabled,
                "last_run": task.last_run,
                "next_run": task.next_run,
            }
            for task in self.tasks.values()
        ]

    def enable_task(self, name: str) -> bool:
        """启用任务"""
        if name in self.tasks:
            self.tasks[name].enabled = True
            return True
        return False

    def disable_task(self, name: str) -> bool:
        """禁用任务"""
        if name in self.tasks:
            self.tasks[name].enabled = False
            return True
        return False

    def run_task(self, name: str) -> bool:
        """手动运行任务"""
        task = self.tasks.get(name)
        if task:
            task.run()
            return True
        return False


# 全局调度器实例
scheduler = TaskScheduler()


def add_scheduled_task(
    name: str, func: Callable, trigger: str = "interval", interval: int = 60, *args, **kwargs
) -> SchedulerTask:
    """
    添加定时任务

    Args:
        name: 任务名称
        func: 任务函数
        trigger: 触发器类型 (interval/cron/date)
        interval: 间隔秒数
        *args: 位置参数
        **kwargs: 关键字参数

    Returns:
        任务实例
    """
    task = SchedulerTask(name=name, func=func, trigger=trigger, interval=interval, args=args, kwargs=kwargs)
    scheduler.add_task(task)
    return task


def remove_scheduled_task(name: str) -> bool:
    """移除定时任务"""
    scheduler.remove_task(name)
    return True


def list_scheduled_tasks() -> List[Dict[str, Any]]:
    """列出所有定时任务"""
    return scheduler.list_tasks()


def run_scheduled_task(name: str) -> bool:
    """手动运行定时任务"""
    return scheduler.run_task(name)
