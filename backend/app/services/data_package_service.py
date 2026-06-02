"""
Data Package Service
数据包管理服务 - 导入导出功能
"""

import hashlib
import json
import os
import shutil
import zipfile
from datetime import timezone, datetime
from decimal import Decimal
from typing import Any, Dict, List, Optional, Tuple

from sqlalchemy.orm import Session

from app.core.exceptions import BusinessError
from app.core.json_encoder import CustomJSONEncoder
from app.core.logging import logger
from app.models.data_package import DataPackage, PackageStatus, PackageType
from app.models.project import Fund, Project
from app.models.school import School
from app.models.village import Village
from app.schemas.data_package import (
    DataPackageConfirmResult,
    DataPackageExportResult,
    DataPackageImportResult,
    DataPackageManifest,
    DataPackagePreviewData,
    DataPackageValidationError,
    DataPackageValidationResult,
    PackageStatusEnum,
)
from app.services.organization_service import OrganizationService

# 支持的数据包版本
SUPPORTED_VERSIONS = ["1.0", "1.1"]
CURRENT_VERSION = "1.0"

# 数据类型映射
DATA_TYPE_MODELS = {
    "villages": Village,
    "projects": Project,
    "funds": Fund,
    "schools": School,
}


class PackageValidationError(BusinessError):
    """数据包验证错误"""

    def __init__(self, errors: List[str]):
        super().__init__(f"数据包验证失败: {', '.join(errors[:3])}")
        self.errors = errors


class PackageVersionUnsupportedError(BusinessError):
    """数据包版本不支持"""

    def __init__(self, version: str):
        super().__init__(f"不支持的数据包版本: {version}")
        self.version = version


class DataPackageService:
    """
    数据包管理服务
    负责数据的导出、导入、验证和预览
    """

    def __init__(self, db: Session, upload_dir: str = None):
        self.db = db
        # 使用可写目录（解决 Windows Program Files 权限问题）
        if upload_dir is None:
            from app.utils.paths import get_app_data_dir

            upload_dir = str(get_app_data_dir() / "uploads" / "packages")
        self.upload_dir = upload_dir
        self.org_service = OrganizationService(db)

        # 确保上传目录存在
        try:
            os.makedirs(upload_dir, exist_ok=True)
        except PermissionError:
            # 回退到用户数据目录
            from app.utils.paths import get_app_data_dir

            upload_dir = str(get_app_data_dir() / "uploads" / "packages")
            os.makedirs(upload_dir, exist_ok=True)
            self.upload_dir = upload_dir

        # 添加日志确认代码已加载
        import logging

        logger = logging.getLogger(__name__)
        logger.info("DataPackageService 初始化，CustomJSONEncoder 已加载")

    # ========================================================================
    # 导出功能
    # ========================================================================

    async def export_package(
        self,
        org_id: int,
        data_types: List[str],
        export_by: int,
        description: str = None,
        package_type: PackageType = PackageType.report,
    ) -> DataPackageExportResult:
        """
        导出数据包

        Args:
            org_id: 组织ID
            data_types: 要导出的数据类型列表
            export_by: 导出人ID
            description: 导出描述
            package_type: 数据包类型 (task: 任务包, report: 上报包)

        Returns:
            导出结果
        """
        # 获取组织信息
        org = self.org_service.get_organization(org_id)
        if not org:
            raise BusinessError(f"组织不存在: {org_id}")

        # 生成包编码
        package_code = self._generate_package_code(org.code, "EXP")

        # 收集数据
        data_dict = {}
        record_counts = {}

        for data_type in data_types:
            if data_type in DATA_TYPE_MODELS:
                model = DATA_TYPE_MODELS[data_type]
                records = self._export_data_type(org_id, model)
                data_dict[data_type] = records
                record_counts[data_type] = len(records)

        # 生成manifest
        manifest = DataPackageManifest(
            version=CURRENT_VERSION,
            package_type=package_type,
            org_code=org.code or f"ORG{org.id:06d}",  # 如果code为None，使用组织ID生成默认编码
            org_name=org.name or f"组织{org.id}",
            export_time=datetime.now(timezone.utc),
            data_types=data_types,
            record_counts=record_counts,
            exported_by=str(export_by),
            description=description,
            checksum="",  # 稍后计算
            encryption="none",  # 加密方式
            compression="zip",  # 压缩方式
            incremental=False,  # 是否增量更新
            base_package_id=None,  # 基础包ID
        )

        # 创建ZIP包
        file_name = f"{package_code}.zip"
        file_path = os.path.join(self.upload_dir, file_name)

        self._create_zip_package(file_path, manifest, data_dict)

        # 计算校验和
        checksum = self._calculate_checksum(file_path)
        manifest.checksum = checksum

        # 获取文件大小
        file_size = os.path.getsize(file_path)

        # 创建数据库记录
        # 将manifest转换为可JSON序列化的字典
        manifest_dict = json.loads(json.dumps(manifest.model_dump(), cls=CustomJSONEncoder))

        package = DataPackage(
            package_code=package_code,
            org_id=org_id,
            file_path=file_path,
            file_name=file_name,
            file_size=file_size,
            manifest=manifest_dict,
            status=PackageStatus.validated.value,
            type=package_type.value,
            version=CURRENT_VERSION,
            checksum=checksum,
            data_types=json.dumps(data_types, cls=CustomJSONEncoder),
            record_count=sum(record_counts.values()),
            created_by=export_by,
        )

        self.db.add(package)
        self.db.commit()
        self.db.refresh(package)

        return DataPackageExportResult(
            package_id=package.id,
            package_code=package_code,
            file_path=file_path,
            file_name=file_name,
            file_size=file_size,
            manifest=manifest,
            download_url=f"/api/v1/data-packages/{package.id}/download",
        )

    def _export_data_type(self, org_id: int, model: Any) -> List[Dict]:
        """导出指定类型的数据"""
        # 根据模型类型查询数据
        query = self.db.query(model)

        # 如果模型有org_id字段，按组织过滤
        if hasattr(model, "org_id"):
            query = query.filter(model.org_id == org_id)

        records = query.all()

        # 转换为字典列表
        result = []
        for record in records:
            record_dict = {}
            for column in record.__table__.columns:
                value = getattr(record, column.name)
                # 处理日期时间类型
                if isinstance(value, datetime):
                    value = value.isoformat()
                # 处理Decimal类型，转换为float
                elif isinstance(value, Decimal):
                    value = float(value)
                # 处理其他可能的非JSON序列化类型
                elif value is not None and not isinstance(value, (str, int, float, bool, list, dict)):
                    value = str(value)
                record_dict[column.name] = value
            result.append(record_dict)

        return result

    def _create_zip_package(
        self,
        file_path: str,
        manifest: DataPackageManifest,
        data_dict: Dict[str, List[Dict]],
    ) -> None:
        """创建ZIP数据包"""
        with zipfile.ZipFile(file_path, "w", zipfile.ZIP_DEFLATED) as zf:
            # 写入manifest
            manifest_json = manifest.model_dump_json(indent=2)
            zf.writestr("manifest.json", manifest_json)

            # 写入数据文件，使用自定义JSON编码器
            for data_type, records in data_dict.items():
                data_json = json.dumps(records, ensure_ascii=False, indent=2, cls=CustomJSONEncoder)
                zf.writestr(f"data/{data_type}.json", data_json)

    # ========================================================================
    # 导入功能
    # ========================================================================

    async def import_package(
        self, file_path: str, file_name: str, org_id: int, imported_by: int
    ) -> DataPackageImportResult:
        """
        导入数据包

        Args:
            file_path: 上传的文件路径
            file_name: 原始文件名
            org_id: 目标组织ID
            imported_by: 导入人ID

        Returns:
            导入结果（包含预览数据）
        """
        # 验证包
        validation = await self.validate_package(file_path)

        if not validation.is_valid:
            # 创建失败记录
            package = self._create_package_record(
                file_path,
                file_name,
                org_id,
                imported_by,
                status=PackageStatus.failed,
                error_message="; ".join([e.message for e in validation.errors]),
            )

            return DataPackageImportResult(
                package_id=package.id,
                package_code=package.package_code,
                status=PackageStatusEnum.failed,
                manifest=validation.manifest,
                preview=[],
                validation=validation,
            )

        # 生成包编码
        package_code = self._generate_package_code(validation.manifest.org_code or "UNKNOWN", "IMP")

        # 移动文件到永久存储
        permanent_path = os.path.join(self.upload_dir, f"{package_code}.zip")
        shutil.copy(file_path, permanent_path)

        # 获取预览数据
        preview = await self.preview_package_data_from_file(permanent_path)

        # 创建数据库记录
        # 将manifest转换为可JSON序列化的字典
        manifest_dict = None
        if validation.manifest:
            manifest_dict = json.loads(json.dumps(validation.manifest.model_dump(), cls=CustomJSONEncoder))

        package = DataPackage(
            package_code=package_code,
            org_id=org_id,
            file_path=permanent_path,
            file_name=file_name,
            file_size=os.path.getsize(permanent_path),
            manifest=manifest_dict,
            status=PackageStatus.validated.value,
            version=validation.manifest.version,
            checksum=self._calculate_checksum(permanent_path),
            data_types=json.dumps(validation.manifest.data_types, cls=CustomJSONEncoder),
            record_count=sum(validation.manifest.record_counts.values()),
            created_by=imported_by,
        )

        self.db.add(package)
        self.db.commit()
        self.db.refresh(package)

        return DataPackageImportResult(
            package_id=package.id,
            package_code=package_code,
            status=PackageStatusEnum.validated,
            manifest=validation.manifest,
            preview=preview,
            validation=validation,
        )

    async def validate_package(self, file_path: str) -> DataPackageValidationResult:
        """
        验证数据包

        Args:
            file_path: 包文件路径

        Returns:
            验证结果
        """
        errors = []
        warnings = []
        manifest = None

        # 检查文件存在
        if not os.path.exists(file_path):
            errors.append(DataPackageValidationError(field="file", message="文件不存在"))
            return DataPackageValidationResult(is_valid=False, errors=errors, warnings=warnings, manifest=None)

        # 检查是否是有效的ZIP文件
        if not zipfile.is_zipfile(file_path):
            errors.append(DataPackageValidationError(field="file", message="不是有效的ZIP文件"))
            return DataPackageValidationResult(is_valid=False, errors=errors, warnings=warnings, manifest=None)

        try:
            with zipfile.ZipFile(file_path, "r") as zf:
                # 检查manifest.json
                if "manifest.json" not in zf.namelist():
                    errors.append(DataPackageValidationError(field="manifest", message="缺少manifest.json文件"))
                    return DataPackageValidationResult(is_valid=False, errors=errors, warnings=warnings, manifest=None)

                # 解析manifest
                manifest_content = zf.read("manifest.json").decode("utf-8")
                manifest_dict = json.loads(manifest_content)

                # 验证版本
                version = manifest_dict.get("version", "unknown")
                if version not in SUPPORTED_VERSIONS:
                    errors.append(DataPackageValidationError(field="version", message=f"不支持的版本: {version}"))

                # 创建manifest对象
                try:
                    manifest = DataPackageManifest(**manifest_dict)
                except Exception as e:
                    errors.append(DataPackageValidationError(field="manifest", message=f"manifest格式错误: {str(e)}"))

                # 验证数据文件
                for data_type in manifest_dict.get("data_types", []):
                    data_file = f"data/{data_type}.json"
                    if data_file not in zf.namelist():
                        errors.append(
                            DataPackageValidationError(
                                field=data_type,
                                message=f"缺少数据文件: {data_file}",
                                data_type=data_type,
                            )
                        )
                    else:
                        # 验证JSON格式
                        try:
                            data_content = zf.read(data_file).decode("utf-8")
                            data = json.loads(data_content)

                            # 验证记录数
                            expected_count = manifest_dict.get("record_counts", {}).get(data_type, 0)
                            actual_count = len(data)
                            if actual_count != expected_count:
                                warnings.append(
                                    f"{data_type}: 记录数不匹配 (期望: {expected_count}, 实际: {actual_count})"
                                )
                        except json.JSONDecodeError as e:
                            errors.append(
                                DataPackageValidationError(
                                    field=data_type,
                                    message=f"JSON格式错误: {str(e)}",
                                    data_type=data_type,
                                )
                            )

        except zipfile.BadZipFile:
            errors.append(DataPackageValidationError(field="file", message="ZIP文件损坏"))
        except Exception as e:
            errors.append(DataPackageValidationError(field="file", message=f"验证失败: {str(e)}"))

        return DataPackageValidationResult(
            is_valid=len(errors) == 0,
            errors=errors,
            warnings=warnings,
            manifest=manifest,
        )

    async def preview_package_data(self, package_id: int) -> List[DataPackagePreviewData]:
        """
        预览导入的数据

        Args:
            package_id: 数据包ID

        Returns:
            预览数据列表
        """
        package = self.db.query(DataPackage).filter(DataPackage.id == package_id).first()

        if not package or not package.file_path:
            return []

        return await self.preview_package_data_from_file(package.file_path)

    async def preview_package_data_from_file(
        self, file_path: str, sample_size: int = 10
    ) -> List[DataPackagePreviewData]:
        """从文件预览数据"""
        preview_list = []

        try:
            with zipfile.ZipFile(file_path, "r") as zf:
                # 读取manifest获取数据类型
                manifest_content = zf.read("manifest.json").decode("utf-8")
                manifest_dict = json.loads(manifest_content)

                for data_type in manifest_dict.get("data_types", []):
                    data_file = f"data/{data_type}.json"
                    if data_file in zf.namelist():
                        data_content = zf.read(data_file).decode("utf-8")
                        data = json.loads(data_content)

                        # 获取列名
                        columns = list(data[0].keys()) if data else []

                        preview_list.append(
                            DataPackagePreviewData(
                                data_type=data_type,
                                total=len(data),
                                sample=data[:sample_size],
                                columns=columns,
                            )
                        )
        except (zipfile.BadZipFile, KeyError, json.JSONDecodeError) as e:
            logger.warning(f"Failed to preview package data from {file_path}: {e}")
        except (IOError, OSError) as e:
            logger.error(f"File I/O error while previewing package: {e}")
        except Exception as e:
            logger.error(f"Unexpected error previewing package data: {e}", exc_info=True)

        return preview_list

    async def confirm_import(
        self,
        package_id: int,
        confirmed_by: int,
        overwrite_existing: bool = False,
        selected_types: List[str] = None,
    ) -> DataPackageConfirmResult:
        """
        确认导入数据

        Args:
            package_id: 数据包ID
            confirmed_by: 确认人ID
            overwrite_existing: 是否覆盖已存在数据
            selected_types: 选择导入的数据类型

        Returns:
            确认结果
        """
        package = self.db.query(DataPackage).filter(DataPackage.id == package_id).first()

        if not package:
            raise BusinessError(f"数据包不存在: {package_id}")

        if package.status != PackageStatus.validated.value:
            raise BusinessError(f"数据包状态不允许导入: {package.status}")

        imported_counts = {}
        skipped_counts = {}
        error_counts = {}
        errors = []

        try:
            with zipfile.ZipFile(package.file_path, "r") as zf:
                manifest_content = zf.read("manifest.json").decode("utf-8")
                manifest_dict = json.loads(manifest_content)

                # 按 org_code 匹配本地组织，解决跨机器 org_id 不一致问题
                resolved_org_id = package.org_id
                source_org_code = manifest_dict.get("org_code", "")
                if source_org_code:
                    from app.models.organization import Organization

                    local_org = self.db.query(Organization).filter(Organization.code == source_org_code).first()
                    if local_org:
                        resolved_org_id = local_org.id

                data_types = selected_types or manifest_dict.get("data_types", [])

                for data_type in data_types:
                    if data_type not in DATA_TYPE_MODELS:
                        continue

                    data_file = f"data/{data_type}.json"
                    if data_file not in zf.namelist():
                        continue

                    data_content = zf.read(data_file).decode("utf-8")
                    records = json.loads(data_content)

                    model = DATA_TYPE_MODELS[data_type]
                    imported, skipped, errs = self._import_records(model, records, resolved_org_id, overwrite_existing)

                    imported_counts[data_type] = imported
                    skipped_counts[data_type] = skipped
                    error_counts[data_type] = len(errs)
                    errors.extend(errs)

            # 更新包状态
            package.status = PackageStatus.imported.value
            package.imported_at = datetime.now(timezone.utc)
            package.imported_by = confirmed_by

            self.db.commit()

            return DataPackageConfirmResult(
                success=True,
                package_id=package_id,
                imported_counts=imported_counts,
                skipped_counts=skipped_counts,
                error_counts=error_counts,
                errors=errors,
            )

        except Exception as e:
            package.status = PackageStatus.failed.value
            package.error_message = str(e)
            self.db.commit()

            return DataPackageConfirmResult(
                success=False,
                package_id=package_id,
                imported_counts=imported_counts,
                skipped_counts=skipped_counts,
                error_counts=error_counts,
                errors=[DataPackageValidationError(field="import", message=str(e))],
            )

    def _import_records(
        self, model: Any, records: List[Dict], org_id: int, overwrite: bool
    ) -> Tuple[int, int, List[DataPackageValidationError]]:
        """导入记录到数据库"""
        imported = 0
        skipped = 0
        errors = []

        for i, record in enumerate(records):
            try:
                # 移除id字段，让数据库自动生成
                record_data = {k: v for k, v in record.items() if k != "id"}

                # 设置组织ID
                if hasattr(model, "org_id"):
                    record_data["org_id"] = org_id

                # 处理日期时间字段
                for key, value in record_data.items():
                    if isinstance(value, str) and "T" in value:
                        try:
                            record_data[key] = datetime.fromisoformat(value.replace("Z", "+00:00"))
                        except ValueError:
                            pass  # nosec B110

                # 创建记录
                obj = model(**record_data)
                self.db.add(obj)
                imported += 1

            except Exception as e:
                errors.append(
                    DataPackageValidationError(
                        field=model.__tablename__,
                        message=str(e),
                        row=i + 1,
                        data_type=model.__tablename__,
                    )
                )

        return imported, skipped, errors

    # ========================================================================
    # 辅助方法
    # ========================================================================

    def _generate_package_code(self, org_code: str, prefix: str) -> str:
        """生成数据包编码"""
        timestamp = datetime.now(timezone.utc).strftime("%Y%m%d%H%M%S")
        # 如果org_code为空或None，使用UNKNOWN
        safe_org_code = org_code if org_code else "UNKNOWN"
        return f"{prefix}-{safe_org_code}-{timestamp}"

    def _calculate_checksum(self, file_path: str) -> str:
        """计算文件SHA256校验和"""
        sha256_hash = hashlib.sha256()
        with open(file_path, "rb") as f:
            for byte_block in iter(lambda: f.read(4096), b""):
                sha256_hash.update(byte_block)
        return f"sha256:{sha256_hash.hexdigest()}"

    def _create_package_record(
        self,
        file_path: str,
        file_name: str,
        org_id: int,
        created_by: int,
        status: PackageStatus,
        error_message: str = None,
    ) -> DataPackage:
        """创建数据包记录"""
        package_code = self._generate_package_code("UNKNOWN", "ERR")

        package = DataPackage(
            package_code=package_code,
            org_id=org_id,
            file_path=file_path,
            file_name=file_name,
            file_size=os.path.getsize(file_path) if os.path.exists(file_path) else 0,
            status=status.value,
            version=CURRENT_VERSION,
            error_message=error_message,
            created_by=created_by,
        )

        self.db.add(package)
        self.db.commit()
        self.db.refresh(package)

        return package

    def get_package(self, package_id: int) -> Optional[DataPackage]:
        """获取数据包"""
        return self.db.query(DataPackage).filter(DataPackage.id == package_id).first()

    def get_packages_by_org(
        self, org_id: int, status: str = None, type_filter: str = None, skip: int = 0, limit: int = 20
    ) -> List[DataPackage]:
        """获取组织的数据包列表"""
        query = self.db.query(DataPackage).filter(DataPackage.org_id == org_id)

        if status:
            query = query.filter(DataPackage.status == status)

        if type_filter:
            query = query.filter(DataPackage.type == type_filter)

        return query.order_by(DataPackage.created_at.desc()).offset(skip).limit(limit).all()

    # ========================================================================
    # 加密导入导出功能
    # ========================================================================

    async def export_encrypted_package(
        self,
        org_id: int,
        data_types: List[str],
        export_by: int,
        password: Optional[str] = None,
        description: str = None,
        package_type: PackageType = PackageType.report,
    ) -> DataPackageExportResult:
        """
        导出加密数据包

        Args:
            org_id: 组织ID
            data_types: 要导出的数据类型列表
            export_by: 导出人ID
            password: 加密密码（可选）
            description: 导出描述

        Returns:
            导出结果
        """
        from app.services.password_encryption_service import PasswordEncryptionService

        # 先导出未加密的数据包
        export_result = await self.export_package(org_id, data_types, export_by, description, package_type)

        # 如果提供了密码，进行加密
        if password:
            original_file_path = export_result.file_path
            encrypted_file_path = original_file_path + ".enc"

            # 加密文件
            salt_hex, iterations = PasswordEncryptionService.encrypt_file(
                original_file_path, password, encrypted_file_path
            )

            # 更新manifest添加加密信息
            manifest_dict = export_result.manifest.model_dump()
            manifest_dict["encryption"] = {
                "enabled": True,
                "algorithm": "aes256-fernet-pbkdf2",
                "salt": salt_hex,
                "iterations": iterations,
            }

            # 使用CustomJSONEncoder序列化manifest
            manifest_json_str = json.dumps(manifest_dict, cls=CustomJSONEncoder)
            manifest_serialized = json.loads(manifest_json_str)

            # 更新数据库记录
            package = self.get_package(export_result.package_id)
            if package:
                package.is_encrypted = True
                package.encryption_algorithm = "aes256-fernet-pbkdf2"
                package.encryption_salt = salt_hex
                package.encryption_iterations = iterations
                package.file_path = encrypted_file_path
                package.file_name = os.path.basename(encrypted_file_path)
                package.file_size = os.path.getsize(encrypted_file_path)
                package.manifest = manifest_serialized
                self.db.commit()

            # 删除未加密的原始文件
            if os.path.exists(original_file_path):
                os.remove(original_file_path)

            # 更新返回结果
            export_result.file_path = encrypted_file_path
            export_result.file_name = os.path.basename(encrypted_file_path)
            export_result.file_size = os.path.getsize(encrypted_file_path)

        return export_result

    async def import_encrypted_package(
        self,
        file_path: str,
        file_name: str,
        org_id: int,
        imported_by: int,
        password: Optional[str] = None,
    ) -> DataPackageImportResult:
        """
        导入加密数据包（预览阶段）

        Args:
            file_path: 上传的文件路径
            file_name: 原始文件名
            org_id: 目标组织ID
            imported_by: 导入人ID
            password: 解密密码（如果文件加密）

        Returns:
            导入预览结果
        """
        from app.services.password_encryption_service import InvalidPasswordError

        decrypted_file_path = file_path
        temp_decrypted_path = None

        try:
            # 检测文件是否加密（尝试直接解压）
            is_encrypted = False
            try:
                with zipfile.ZipFile(file_path, "r") as zf:
                    # 尝试读取manifest
                    zf.read("manifest.json")
            except (zipfile.BadZipFile, KeyError):
                # 无法解压，可能是加密文件
                is_encrypted = True

            # 如果是加密文件，需要解密
            if is_encrypted:
                if not password:
                    raise BusinessError("该数据包已加密，请提供密码")

                # 尝试从文件名或临时记录获取加密信息
                # 这里简化处理：先尝试解密，如果失败则提示密码错误
                temp_decrypted_path = file_path + ".decrypted"

                # 尝试使用默认参数解密
                try:
                    # 从加密文件中提取盐值（实际应该从manifest或数据库获取）
                    # 这里我们需要先部分解密或从其他地方获取盐值
                    # 简化处理：假设使用标准迭代次数
                    raise BusinessError("需要先上传文件获取加密参数，请使用两步导入流程")
                except InvalidPasswordError:
                    raise BusinessError("密码错误，请检查后重试")

            # 调用原有的导入方法
            return await self.import_package(decrypted_file_path, file_name, org_id, imported_by)

        finally:
            # 清理临时解密文件
            if temp_decrypted_path and os.path.exists(temp_decrypted_path):
                os.remove(temp_decrypted_path)

    async def decrypt_and_preview_package(self, package_id: int, password: str) -> DataPackageImportResult:
        """
        解密并预览数据包

        Args:
            package_id: 数据包ID
            password: 解密密码

        Returns:
            导入预览结果
        """
        from app.services.password_encryption_service import (
            InvalidPasswordError,
            PasswordEncryptionService,
        )

        package = self.get_package(package_id)
        if not package:
            raise BusinessError(f"数据包不存在: {package_id}")

        if not package.is_encrypted:
            raise BusinessError("该数据包未加密，无需解密")

        encrypted_file_path = package.file_path
        temp_decrypted_path = encrypted_file_path + ".decrypted"

        try:
            # 解密文件
            PasswordEncryptionService.decrypt_file(
                encrypted_file_path,
                password,
                package.encryption_salt,
                package.encryption_iterations,
                temp_decrypted_path,
            )

            # 验证解密后的文件
            validation_result = await self.validate_package(temp_decrypted_path)

            if not validation_result.is_valid:
                raise PackageValidationError(validation_result.errors)

            # 返回预览数据
            return DataPackageImportResult(
                package_id=package.id,
                package_code=package.package_code,
                status=PackageStatusEnum.VALIDATED,
                manifest=validation_result.manifest,
                preview_data=None,  # 简化处理，不返回详细预览
                validation_errors=[],
            )

        except InvalidPasswordError:
            raise BusinessError("密码错误，请检查后重试")
        finally:
            # 清理临时文件
            if os.path.exists(temp_decrypted_path):
                os.remove(temp_decrypted_path)

    async def confirm_import_with_conflict_resolution(
        self,
        package_id: int,
        conflict_strategy: str = "KEEP_BOTH",
        password: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        确认导入并处理冲突

        Args:
            package_id: 数据包ID
            conflict_strategy: 冲突解决策略
            password: 解密密码（如果包已加密）

        Returns:
            导入结果
        """
        from app.services.smart_conflict_resolver import SmartConflictResolver
        from app.services.password_encryption_service import (
            PasswordEncryptionService,
            InvalidPasswordError,
        )

        package = self.get_package(package_id)
        if not package:
            raise BusinessError(f"数据包不存在: {package_id}")

        if package.status != PackageStatus.validated.value:
            raise BusinessError(f"数据包状态不正确: {package.status}")

        # 解密文件（如果需要）
        file_path = package.file_path
        temp_decrypted_path = None

        try:
            if package.is_encrypted:
                if not password:
                    raise BusinessError("加密包需要提供密码才能导入")

                # 解密文件
                temp_decrypted_path = file_path + ".temp_decrypted"
                try:
                    PasswordEncryptionService.decrypt_file(
                        file_path,
                        password,
                        package.encryption_salt,
                        package.encryption_iterations,
                        temp_decrypted_path,
                    )
                    file_path = temp_decrypted_path
                except InvalidPasswordError:
                    raise BusinessError("密码错误，请检查后重试")

            # 读取数据包
            with zipfile.ZipFile(file_path, "r") as zf:
                # 读取manifest
                manifest_json = zf.read("manifest.json").decode("utf-8")
                manifest = json.loads(manifest_json)

                # 读取数据
                data_dict = {}
                for data_type in manifest.get("data_types", []):
                    try:
                        data_json = zf.read(f"data/{data_type}.json").decode("utf-8")
                        data_dict[data_type] = json.loads(data_json)
                    except KeyError:
                        continue

            # 使用智能冲突解决器导入
            resolver = SmartConflictResolver(self.db)
            id_mapping = resolver.import_with_id_mapping(data_dict, conflict_strategy)

            # 提交事务
            self.db.commit()

            # 更新包状态
            package.status = PackageStatus.imported.value
            package.imported_at = datetime.now(timezone.utc)
            package.imported_by = package.created_by  # 这里应该传入实际的导入人ID
            self.db.commit()

            # 统计导入数量
            imported_counts = {data_type: len(mapping) for data_type, mapping in id_mapping.items()}

            return {
                "success": True,
                "imported_counts": imported_counts,
                "id_mapping": id_mapping,
                "message": f"成功导入 {sum(imported_counts.values())} 条记录",
            }

        except Exception as e:
            self.db.rollback()
            package.status = PackageStatus.failed.value
            package.error_message = str(e)
            self.db.commit()
            raise

        finally:
            if temp_decrypted_path and os.path.exists(temp_decrypted_path):
                os.remove(temp_decrypted_path)
