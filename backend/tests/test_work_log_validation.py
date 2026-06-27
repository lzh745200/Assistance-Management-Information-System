"""
测试工作日志验证修复
"""
import pytest




def test_create_work_log_with_empty_string(client, user_headers):
    """测试: 发送空字符串应该返回422错误"""
    response = client.post(
        "/api/v1/work-logs",
        json={
            "work_date": "2026-03-14",
            "content": ""
        },
        headers=user_headers
    )

    assert response.status_code == 422
    assert "工作内容不能为空" in response.json()["detail"]


def test_create_work_log_with_whitespace_only(client, user_headers):
    """测试: 发送只有空格的字符串应该返回422错误"""
    response = client.post(
        "/api/v1/work-logs",
        json={
            "work_date": "2026-03-14",
            "content": "   "
        },
        headers=user_headers
    )

    assert response.status_code == 422
    assert "工作内容不能为空" in response.json()["detail"]


def test_create_work_log_with_valid_content(client, user_headers):
    """测试: 发送正常内容应该成功"""
    response = client.post(
        "/api/v1/work-logs",
        json={
            "work_date": "2026-03-14",
            "content": "完成项目进度检查"
        },
        headers=user_headers
    )

    assert response.status_code == 200
    data = response.json()
    assert data["content"] == "完成项目进度检查"
    assert data["log_date"] == "2026-03-14"


def test_create_work_log_with_content_having_leading_trailing_spaces(client, user_headers):
    """测试: 内容前后有空格应该自动去除"""
    response = client.post(
        "/api/v1/work-logs",
        json={
            "work_date": "2026-03-14",
            "content": "  完成项目进度检查  "
        },
        headers=user_headers
    )

    assert response.status_code == 200
    data = response.json()
    # 验证空格已被去除
    assert data["content"] == "完成项目进度检查"


def test_create_work_log_with_title_fallback(client, user_headers):
    """测试: 使用 title 字段作为 content 的后备"""
    response = client.post(
        "/api/v1/work-logs",
        json={
            "work_date": "2026-03-14",
            "title": "项目会议"
        },
        headers=user_headers
    )

    assert response.status_code == 200
    data = response.json()
    # title 应该被转换为 content
    assert data["content"] == "项目会议"


def test_create_work_log_without_date(client, user_headers):
    """测试: 不提供日期应该返回422错误"""
    response = client.post(
        "/api/v1/work-logs",
        json={
            "content": "完成项目进度检查"
        },
        headers=user_headers
    )

    assert response.status_code == 422
    assert "工作日期不能为空" in response.json()["detail"]


def test_create_work_log_with_optional_fields(client, user_headers):
    """测试: 可选字段可以为空"""
    response = client.post(
        "/api/v1/work-logs",
        json={
            "work_date": "2026-03-14",
            "content": "完成项目进度检查",
            "category": "",  # 可选字段可以为空
            "location": "",
            "participants": ""
        },
        headers=user_headers
    )

    assert response.status_code == 200
    data = response.json()
    assert data["content"] == "完成项目进度检查"


def test_pydantic_validation_allows_none(client, user_headers):
    """测试: Pydantic 验证允许 None 值"""
    # 不发送 content 字段(None)
    response = client.post(
        "/api/v1/work-logs",
        json={
            "work_date": "2026-03-14"
        },
        headers=user_headers
    )

    # 应该通过 Pydantic 验证,但在业务逻辑中被拒绝
    assert response.status_code == 422
    assert "工作内容不能为空" in response.json()["detail"]


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
