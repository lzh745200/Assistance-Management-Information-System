"""Project model factories."""

from datetime import datetime, timezone, date

from app.models.project import Project, ProjectTask, ProjectFile


class ProjectFactory:
    @staticmethod
    def build(**kwargs):
        now = datetime.now(timezone.utc)
        data = dict(
            name="测试项目",
            code="PRJ-" + str(id(now))[-6:],
            type="infrastructure",
            status="draft",
            description="这是一个测试项目",
            priority="medium",
            budget=100000.00,
            actual_cost=0,
            progress=0,
            start_date=date(2024, 1, 1),
            end_date=date(2024, 12, 31),
            created_at=now,
            updated_at=now,
        )
        data.update(kwargs)
        return Project(**data)

    @staticmethod
    def create(db, **kwargs):
        obj = ProjectFactory.build(**kwargs)
        db.add(obj)
        db.flush()
        return obj

    @staticmethod
    def create_with_tasks(db, task_count=3, **kwargs):
        project = ProjectFactory.create(db, **kwargs)
        tasks = []
        for i in range(task_count):
            task = ProjectTaskFactory.create(db, project_id=project.id,
                                              name=f"任务{i+1}")
            tasks.append(task)
        return project, tasks

    @staticmethod
    def build_approved(**kwargs):
        kwargs.setdefault("status", "approved")
        return ProjectFactory.build(**kwargs)

    @staticmethod
    def build_completed(**kwargs):
        kwargs.setdefault("status", "completed")
        kwargs.setdefault("progress", 100)
        kwargs.setdefault("actual_cost", 95000.00)
        return ProjectFactory.build(**kwargs)


class ProjectTaskFactory:
    @staticmethod
    def build(project_id=1, **kwargs):
        now = datetime.now(timezone.utc)
        data = dict(
            project_id=project_id,
            name="测试任务",
            description="测试任务描述",
            status="pending",
            priority="medium",
            assignee="测试人",
            created_at=now,
            updated_at=now,
        )
        data.update(kwargs)
        return ProjectTask(**data)

    @staticmethod
    def create(db, project_id=1, **kwargs):
        obj = ProjectTaskFactory.build(project_id=project_id, **kwargs)
        db.add(obj)
        db.flush()
        return obj


class ProjectFileFactory:
    @staticmethod
    def build(project_id=1, **kwargs):
        now = datetime.now(timezone.utc)
        data = dict(
            project_id=project_id,
            category="document",
            filename="test.docx",
            filepath="/uploads/test.docx",
            file_size=1024,
            uploaded_by=1,
            created_at=now,
        )
        data.update(kwargs)
        return ProjectFile(**data)

    @staticmethod
    def create(db, project_id=1, **kwargs):
        obj = ProjectFileFactory.build(project_id=project_id, **kwargs)
        db.add(obj)
        db.flush()
        return obj
