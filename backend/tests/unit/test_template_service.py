"""模板服务单元测试

TemplateService 各方法已改为 raise NotImplementedError（此前为内存字典
不持久化 + 渲染为空操作，未接入路由）。测试验证各方法正确抛出异常。
"""
import pytest
import asyncio


def run_async(coro):
    return asyncio.run(coro)


@pytest.fixture
def svc():
    from app.services.template_service import TemplateService
    return TemplateService()


def test_init(svc):
    # __init__ 仍保留 _templates 字典以兼容历史，但不再用于业务逻辑
    assert svc._templates == {}


def test_get_templates_empty(svc):
    with pytest.raises(NotImplementedError):
        run_async(svc.get_templates())


def test_create_template(svc):
    with pytest.raises(NotImplementedError):
        run_async(svc.create_template({"name": "test", "type": "report", "content": "hello"}))


def test_get_template_after_create(svc):
    with pytest.raises(NotImplementedError):
        run_async(svc.get_template(1))


def test_get_templates_with_filter(svc):
    with pytest.raises(NotImplementedError):
        run_async(svc.get_templates(template_type="report"))


def test_delete_template(svc):
    with pytest.raises(NotImplementedError):
        run_async(svc.delete_template(1))
