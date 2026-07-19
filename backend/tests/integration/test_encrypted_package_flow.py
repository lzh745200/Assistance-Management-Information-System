"""
Encrypted Package Flow Integration Tests
"""

import pytest


import os
import tempfile
import uuid
from sqlalchemy.orm import Session
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.models.village import Village
from app.models.organization import Organization
from app.services.data_package_service import DataPackageService


@pytest.fixture(scope="function")
def real_db_session():
    """创建真实的数据库会话（使用内存数据库避免文件锁定和超时）"""
    engine = create_engine("sqlite:///:memory:", connect_args={"check_same_thread": False})

    # 使用内存数据库创建所有表（内存数据库速度快，不会超时）
    from app.models.base import Base
    Base.metadata.create_all(bind=engine)

    SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    session = SessionLocal()

    yield session

    # Cleanup
    session.close()
    engine.dispose()


class TestEncryptedPackageFlow:
    """加密数据包完整流程测试"""

    @pytest.fixture
    def test_org(self, real_db_session: Session):
        """创建测试组织"""
        org = Organization(
            name="测试组织",
            code=f"TEST_ORG_{uuid.uuid4().hex[:8]}",
            type="military",
        )
        real_db_session.add(org)
        real_db_session.commit()
        real_db_session.refresh(org)
        return org

    @pytest.fixture
    def service(self, real_db_session: Session):
        """创建数据包服务实例"""
        temp_dir = tempfile.mkdtemp()
        return DataPackageService(real_db_session, upload_dir=temp_dir)

    @pytest.fixture
    def test_villages(self, real_db_session: Session):
        """创建测试村庄数据"""
        # 清理可能存在的测试数据
        real_db_session.query(Village).filter(Village.code.like("V00%")).delete()
        real_db_session.commit()

        villages = [
            Village(code="V001", name="测试村1", province="省1", city="市1"),
            Village(code="V002", name="测试村2", province="省1", city="市1"),
            Village(code="V003", name="测试村3", province="省2", city="市2"),
        ]
        for village in villages:
            real_db_session.add(village)
        real_db_session.commit()
        return villages

    @pytest.mark.asyncio
    async def test_export_unencrypted_package(
        self, service: DataPackageService, test_org: Organization, test_villages
    ):
        """测试导出未加密数据包"""
        result = await service.export_encrypted_package(
            org_id=test_org.id,
            data_types=["villages"],
            export_by=1,
            password=None,  # 不加密
            description="测试导出"
        )

        assert result.package_id > 0
        assert result.file_name.endswith(".zip")
        assert os.path.exists(result.file_path)
        assert result.file_size > 0

        # 验证数据包记录
        package = service.get_package(result.package_id)
        assert package is not None
        assert package.is_encrypted is False or package.is_encrypted is None

    @pytest.mark.asyncio
    async def test_export_encrypted_package(
        self, service: DataPackageService, test_org: Organization, test_villages
    ):
        """测试导出加密数据包"""
        password = "test_password_123"

        result = await service.export_encrypted_package(
            org_id=test_org.id,
            data_types=["villages"],
            export_by=1,
            password=password,
            description="加密测试导出"
        )

        assert result.package_id > 0
        assert result.file_name.endswith(".enc")
        assert os.path.exists(result.file_path)

        # 验证数据包记录
        package = service.get_package(result.package_id)
        assert package is not None
        assert package.is_encrypted is True
