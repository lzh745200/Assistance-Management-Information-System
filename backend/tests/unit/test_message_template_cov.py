"""app.models.message_template 覆盖率攻坚测试

直接实例化 MessageTemplate 调用 render_* 方法，
覆盖变量渲染、KeyError 回退、邮件模板为空时回退到站内模板三个分支。
"""

from app.models.message_template import MessageTemplate


def _tpl(**overrides):
    base = dict(
        code="t1",
        name="测试模板",
        message_type="system",
        title_template="标题:{name}",
        content_template="内容:{name}",
        email_subject_template=None,
        email_body_template=None,
    )
    base.update(overrides)
    return MessageTemplate(**base)


class TestRenderTitle:
    def test_with_variables(self):
        assert _tpl().render_title({"name": "张三"}) == "标题:张三"

    def test_missing_variable_returns_raw_template(self):
        assert _tpl().render_title({}) == "标题:{name}"


class TestRenderContent:
    def test_with_variables(self):
        assert _tpl().render_content({"name": "张三"}) == "内容:张三"

    def test_missing_variable_returns_raw_template(self):
        assert _tpl().render_content({}) == "内容:{name}"


class TestRenderEmailSubject:
    def test_fallback_to_title_when_no_subject_template(self):
        assert _tpl().render_email_subject({"name": "张三"}) == "标题:张三"

    def test_with_subject_template(self):
        tpl = _tpl(email_subject_template="主题:{name}")
        assert tpl.render_email_subject({"name": "张三"}) == "主题:张三"

    def test_missing_variable_returns_raw_template(self):
        tpl = _tpl(email_subject_template="主题:{name}")
        assert tpl.render_email_subject({}) == "主题:{name}"


class TestRenderEmailBody:
    def test_fallback_to_content_when_no_body_template(self):
        assert _tpl().render_email_body({"name": "张三"}) == "内容:张三"

    def test_with_body_template(self):
        tpl = _tpl(email_body_template="正文:{name}")
        assert tpl.render_email_body({"name": "张三"}) == "正文:张三"

    def test_missing_variable_returns_raw_template(self):
        tpl = _tpl(email_body_template="正文:{name}")
        assert tpl.render_email_body({}) == "正文:{name}"


class TestRepr:
    def test_repr_contains_key_fields(self):
        tpl = _tpl()
        assert repr(tpl) == "<MessageTemplate(id=None, code='t1', name='测试模板')>"
