"""
Data Package Encrypted Schemas
数据包加密相关的Pydantic模式
"""

from typing import List, Optional

from pydantic import BaseModel, Field, field_validator


class DataPackageExportEncryptedRequest(BaseModel):
    """加密导出请求"""

    data_types: List[str] = Field(..., description="要导出的数据类型")
    password: Optional[str] = Field(None, description="加密密码（可选）")
    description: Optional[str] = Field(None, description="导出描述")

    @field_validator("data_types")
    @classmethod
    def validate_data_types(cls, v):
        """验证数据类型"""
        allowed_types = {"villages", "projects", "funds", "schools"}
        for dt in v:
            if dt not in allowed_types:
                raise ValueError(f"不支持的数据类型: {dt}")
        return v

    @field_validator("password")
    @classmethod
    def validate_password(cls, v):
        """验证密码强度"""
        if v is not None and len(v) < 8:
            raise ValueError("密码长度至少8位")
        return v


class DataPackageImportEncryptedRequest(BaseModel):
    """加密导入请求"""

    password: Optional[str] = Field(None, description="解密密码")
    org_id: Optional[int] = Field(None, description="目标组织ID")
    conflict_strategy: str = Field("KEEP_BOTH", description="冲突解决策略")

    @field_validator("conflict_strategy")
    @classmethod
    def validate_strategy(cls, v):
        """验证冲突策略"""
        allowed_strategies = {"SKIP", "OVERWRITE", "KEEP_BOTH", "MERGE"}
        if v not in allowed_strategies:
            raise ValueError(f"不支持的冲突策略: {v}")
        return v


class EncryptionInfo(BaseModel):
    """加密信息"""

    enabled: bool = Field(..., description="是否启用加密")
    algorithm: Optional[str] = Field(None, description="加密算法")
    salt: Optional[str] = Field(None, description="盐值(hex)")
    iterations: Optional[int] = Field(None, description="PBKDF2迭代次数")


class ConflictInfo(BaseModel):
    """冲突信息"""

    data_type: str = Field(..., description="数据类型")
    business_key: dict = Field(..., description="业务唯一键")
    differences: List[str] = Field(..., description="差异字段���表")
    local_data: dict = Field(..., description="本地数据")
    import_data: dict = Field(..., description="导入数据")


class ImportPreviewResult(BaseModel):
    """导入预览结果"""

    package_id: int = Field(..., description="数据包ID")
    is_encrypted: bool = Field(..., description="是否加密")
    manifest: dict = Field(..., description="清单信息")
    new_records_count: int = Field(..., description="新记录数量")
    conflict_records_count: int = Field(..., description="冲突记录数量")
    conflicts: List[ConflictInfo] = Field(default_factory=list, description="冲突详情")


class ImportConfirmRequest(BaseModel):
    """导入确认请求"""

    package_id: int = Field(..., description="数据包ID")
    conflict_strategy: str = Field("KEEP_BOTH", description="冲突解决策略")

    @field_validator("conflict_strategy")
    @classmethod
    def validate_strategy(cls, v):
        """验证冲突策略"""
        allowed_strategies = {"SKIP", "OVERWRITE", "KEEP_BOTH", "MERGE"}
        if v not in allowed_strategies:
            raise ValueError(f"不支持的冲突策略: {v}")
        return v


class ImportConfirmResult(BaseModel):
    """导入确认结果"""

    success: bool = Field(..., description="是否成功")
    imported_counts: dict = Field(..., description="导入数量统计")
    id_mapping: dict = Field(..., description="ID映射表")
    message: str = Field(..., description="结果消息")


class EncryptedDataPackage(BaseModel):
    """加密数据包"""

    id: int = Field(..., description="数据包ID")
    name: str = Field(..., description="数据包名称")
    description: Optional[str] = Field(None, description="描述")
    is_encrypted: bool = Field(True, description="是否加密")
    encryption_algorithm: Optional[str] = Field(None, description="加密算法")
    file_size: Optional[int] = Field(None, description="文件大小(字节)")
    created_at: Optional[str] = Field(None, description="创建时间")
    created_by: Optional[int] = Field(None, description="创建者ID")
