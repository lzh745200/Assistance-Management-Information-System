"""模板服务单元测试"""
import pytest
import asyncio

def run_async(coro):
    return asyncio.run(coro)

@pytest.fixture
def svc():
    from app.services.template_service import TemplateService
    return TemplateService()

def test_init(svc):
    assert svc._templates == {}

def test_get_templates_empty(svc):
    result = run_async(svc.get_templates())
    assert result == []

def test_create_template(svc):
    data = {"name": "test", "type": "report", "content": "hello"}
    result = run_async(svc.create_template(data))
    assert result["name"] == "test"
    assert result["id"] is not None

def test_get_template_after_create(svc):
    data = {"name": "t2", "type": "report"}
    created = run_async(svc.create_template(data))
    found = run_async(svc.get_template(created["id"]))
    assert found is not None
    assert found["name"] == "t2"

def test_get_templates_with_filter(svc):
    run_async(svc.create_template({"name": "a", "type": "report"}))
    run_async(svc.create_template({"name": "b", "type": "dashboard"}))
    reports = run_async(svc.get_templates(template_type="report"))
    assert len(reports) >= 1
    for r in reports:
        assert r["type"] == "report"

def test_delete_template(svc):
    created = run_async(svc.create_template({"name": "del_me"}))
    result = run_async(svc.delete_template(created["id"]))
    assert result is True
    assert run_async(svc.get_template(created["id"])) is None
