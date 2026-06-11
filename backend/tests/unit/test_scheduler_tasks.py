"""Tests for app/utils/scheduler_tasks.py — 100% coverage."""
import logging
from unittest.mock import MagicMock, patch

import pytest

from app.utils.scheduler_tasks import (
    SchedulerTask,
    TaskScheduler,
    add_scheduled_task,
    list_scheduled_tasks,
    remove_scheduled_task,
    run_scheduled_task,
    scheduler,
)


# ---------------------------------------------------------------------------
# SchedulerTask
# ---------------------------------------------------------------------------


class TestSchedulerTaskInit:
    def test_default_args(self):
        task = SchedulerTask(name="test", func=lambda: None)
        assert task.name == "test"
        assert task.trigger == "interval"
        assert task.interval == 60
        assert task.args == ()
        assert task.kwargs == {}
        assert task.enabled is True
        assert task.last_run is None
        assert task.next_run is None

    def test_custom_args(self):
        task = SchedulerTask(
            name="custom", func=lambda x, y: None, trigger="cron", interval=300,
            args=(1,), kwargs={"y": 2},
        )
        assert task.args == (1,)
        assert task.kwargs == {"y": 2}
        assert task.trigger == "cron"
        assert task.interval == 300

    def test_none_args_kwargs_default_to_empty(self):
        task = SchedulerTask(name="n", func=lambda: None, args=None, kwargs=None)
        assert task.args == ()
        assert task.kwargs == {}


class TestSchedulerTaskRun:
    def test_run_calls_func_updates_last_run(self):
        func = MagicMock()
        task = SchedulerTask(name="t", func=func)
        task.run()
        func.assert_called_once_with()
        assert task.last_run is not None

    def test_run_disabled_does_nothing(self):
        func = MagicMock()
        task = SchedulerTask(name="t", func=func)
        task.enabled = False
        task.run()
        func.assert_not_called()
        assert task.last_run is None

    def test_run_exception_logged(self, caplog):
        func = MagicMock(side_effect=ValueError("boom"))
        caplog.set_level(logging.ERROR)
        task = SchedulerTask(name="failing", func=func)
        task.run()
        assert "执行失败" in caplog.text


# ---------------------------------------------------------------------------
# TaskScheduler
# ---------------------------------------------------------------------------


class TestTaskScheduler:
    def make_scheduler(self):
        s = TaskScheduler()
        s.add_task(SchedulerTask(name="a", func=lambda: None))
        s.add_task(SchedulerTask(name="b", func=lambda: None))
        return s

    def test_add_task(self):
        s = TaskScheduler()
        t = SchedulerTask(name="x", func=lambda: None)
        s.add_task(t)
        assert s.tasks["x"] is t

    def test_remove_task_exists(self):
        s = self.make_scheduler()
        s.remove_task("a")
        assert "a" not in s.tasks

    def test_remove_task_not_exists_no_error(self):
        s = TaskScheduler()
        s.remove_task("nonexistent")

    def test_get_task_exists(self):
        s = self.make_scheduler()
        t = s.get_task("a")
        assert t is not None
        assert t.name == "a"

    def test_get_task_not_exists_returns_none(self):
        s = TaskScheduler()
        assert s.get_task("nonexistent") is None

    def test_list_tasks(self):
        s = self.make_scheduler()
        lst = s.list_tasks()
        assert len(lst) == 2
        names = [t["name"] for t in lst]
        assert "a" in names
        assert "b" in names
        for t in lst:
            assert "trigger" in t
            assert "interval" in t
            assert "enabled" in t
            assert "last_run" in t
            assert "next_run" in t

    def test_enable_task_exists(self):
        s = self.make_scheduler()
        s.tasks["a"].enabled = False
        assert s.enable_task("a") is True
        assert s.tasks["a"].enabled is True

    def test_enable_task_not_exists(self):
        s = TaskScheduler()
        assert s.enable_task("x") is False

    def test_disable_task_exists(self):
        s = self.make_scheduler()
        assert s.disable_task("a") is True
        assert s.tasks["a"].enabled is False

    def test_disable_task_not_exists(self):
        s = TaskScheduler()
        assert s.disable_task("x") is False

    def test_run_task_exists(self):
        s = self.make_scheduler()
        s.tasks["a"].func = MagicMock()
        assert s.run_task("a") is True
        s.tasks["a"].func.assert_called_once()

    def test_run_task_not_exists(self):
        s = TaskScheduler()
        assert s.run_task("x") is False


# ---------------------------------------------------------------------------
# Module-level functions & singleton
# ---------------------------------------------------------------------------


class TestModuleFunctions:

    def teardown_method(self):
        scheduler.tasks.clear()

    def test_add_scheduled_task_returns_task(self):
        t = add_scheduled_task("m1", func=lambda: None, trigger="interval", interval=30)
        assert isinstance(t, SchedulerTask)
        assert t.name == "m1"
        assert t.trigger == "interval"
        assert t.interval == 30
        assert "m1" in scheduler.tasks

    def test_add_scheduled_task_with_args(self):
        func = MagicMock()
        t = add_scheduled_task("m2", func, "cron", 120, "arg1", key="val")
        assert t.args == ("arg1",)
        assert t.kwargs == {"key": "val"}

    def test_remove_scheduled_task(self):
        add_scheduled_task("r1", func=lambda: None)
        result = remove_scheduled_task("r1")
        assert result is True
        assert "r1" not in scheduler.tasks

    def test_list_scheduled_tasks(self):
        add_scheduled_task("l1", func=lambda: None)
        add_scheduled_task("l2", func=lambda: None)
        tasks = list_scheduled_tasks()
        assert len(tasks) == 2

    def test_run_scheduled_task_exists(self):
        func = MagicMock()
        add_scheduled_task("run1", func)
        result = run_scheduled_task("run1")
        assert result is True
        func.assert_called_once()

    def test_run_scheduled_task_not_exists(self):
        result = run_scheduled_task("nonexistent")
        assert result is False

    def test_scheduler_is_singleton(self):
        from app.utils.scheduler_tasks import scheduler as s1, TaskScheduler
        assert isinstance(s1, TaskScheduler)

    def test_scheduler_initial_empty(self):
        assert scheduler.tasks == {}
        assert scheduler._running is False
