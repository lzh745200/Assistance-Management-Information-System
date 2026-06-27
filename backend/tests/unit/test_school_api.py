"""学校 API 基础测试"""

class TestSchoolModel:
    """学校模型字段验证"""

    def test_school_model_fields(self):
        """验证 School 模型定义了必要字段"""
        from app.models.school import School
        cols = {c.name for c in School.__table__.columns}
        required = {"id", "name", "type", "address"}
        assert required.issubset(cols), f"缺少必要字段: {required - cols}"

    def test_school_model_has_org_fields(self):
        """验证 School 模型有组织关联字段"""
        from app.models.school import School
        cols = {c.name for c in School.__table__.columns}
        assert "organization_id" in cols, "缺少 organization_id 字段"

class TestSchoolSchema:
    """学校 Schema 验证"""

    def test_school_create_schema(self):
        """验证 SchoolCreate schema"""
        from app.schemas.school import SchoolCreate
        from app.models.school import SchoolType, SchoolLevel

        data = SchoolCreate(
            name="测试学校",
            code="TEST001",
            school_type=SchoolType.PRIMARY,
            school_level=SchoolLevel.PROVINCIAL,
        )
        assert data.name == "测试学校"
        assert data.code == "TEST001"

    def test_school_create_defaults(self):
        """验证 SchoolCreate 默认值"""
        from app.schemas.school import SchoolCreate
        from app.models.school import SchoolType, SchoolLevel

        data = SchoolCreate(
            name="测试学校",
            code="TEST001",
            school_type=SchoolType.PRIMARY,
            school_level=SchoolLevel.PROVINCIAL,
        )
        assert data.has_library is False
        assert data.is_active_support is True

class TestSchoolRouterRegistration:
    """学校路由注册"""

    def test_router_exists(self):
        """验证学校路由已注册"""
        from app.api.v1.school import router
        assert router is not None

    def test_router_has_endpoints(self):
        """验证学校路由包含基本端点"""
        from app.api.v1.school import router
        paths = {r.path for r in router.routes}
        assert "/schools" in paths, f"缺少 GET /schools 端点，现有路径: {paths}"
        assert "/schools/{school_id}" in paths, "缺少 GET/PUT /schools/{id} 端点"
