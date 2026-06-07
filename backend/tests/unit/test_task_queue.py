"""任务队列单元测试"""
import pytest

class TestTaskStatus:
    def test_enum_values(self):
        from app.services.task_queue import TaskStatus
        assert TaskStatus.PENDING == "pending"
        assert TaskStatus.RUNNING == "running"
        assert TaskStatus.COMPLETED == "completed"
        assert TaskStatus.FAILED == "failed"
        assert TaskStatus.CANCELLED == "cancelled"

class TestTaskPriority:
    def test_enum_values(self):
        from app.services.task_queue import TaskPriority
        assert TaskPriority.LOW == 10
        assert TaskPriority.NORMAL == 5
        assert TaskPriority.HIGH == 1

class TestTask:
    def test_create_task(self):
        from app.services.task_queue import Task, TaskPriority
        t = Task(name="test", func=lambda: 42, priority=TaskPriority.NORMAL)
        assert t.name == "test"
        assert t.priority == TaskPriority.NORMAL
        assert t.id is not None
        assert t.status == "pending"

    def test_task_to_dict(self):
        from app.services.task_queue import Task, TaskPriority
        t = Task(name="test", func=lambda: 42)
        d = t.to_dict()
        assert d["name"] == "test"
        assert "status" in d

class TestTaskQueueInstance:
    def test_task_queue_class_exists(self):
        from app.services.task_queue import TaskQueue
        assert TaskQueue is not None
