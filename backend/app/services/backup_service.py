"""
系统备份服务（增强版）
新增功能：增量备份、备份验证、备份加密、备份压缩级别配置
"""

import hashlib
import json
import logging
import os
import shutil
import sqlite3
import tempfile
import zipfile
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional

from sqlalchemy.orm import Session

from app.models.system_config import SystemConfig

logger = logging.getLogger(__name__)


class BackupRestoreError(Exception):
    """备份恢复失败异常"""

    def __init__(self, message: str):
        self.message = message
        super().__init__(message)


class BackupRecord:
    """备份记录"""

    def __init__(
        self,
        backup_id: int,
        file_name: str,
        file_path: str,
        file_size: int,
        description: str,
        created_at: datetime,
        backup_type: str = "full",  # full, incremental
        checksum: Optional[str] = None,
    ):
        self.backup_id = backup_id
        self.file_name = file_name
        self.file_path = file_path
        self.file_size = file_size
        self.description = description
        self.created_at = created_at
        self.backup_type = backup_type
        self.checksum = checksum


class BackupService:
    """系统备份服务"""

    def __init__(self, db: Session, backup_dir: str = None):
        self.db = db
        # 使用配置中的备份目录或动态计算用户可写路径
        if backup_dir is None:
            from app.utils.paths import get_backup_path

            self.backup_dir = str(get_backup_path())
        else:
            self.backup_dir = backup_dir
        # 数据库路径使用统一的路径工具模块
        from app.utils.paths import get_database_path

        self.database_path = str(get_database_path().absolute())
        # 上传目录也使用动态路径
        from app.utils.paths import get_uploads_path

        self.uploads_dir = str(get_uploads_path())

        # 确保备份目录存在
        os.makedirs(self.backup_dir, exist_ok=True)

        # 增量备份配置
        self.incremental_enabled = os.getenv("INCREMENTAL_BACKUP_ENABLED", "true").lower() == "true"
        self.compression_level = int(os.getenv("BACKUP_COMPRESSION_LEVEL", "6"))  # 0-9
        self.last_backup_manifest = self._load_last_manifest()

    def _validate_path(self, file_path: str) -> bool:
        """
        验证路径安全性，防止路径遍历攻击

        Args:
            file_path: 要验证的文件路径

        Returns:
            路径是否安全
        """
        try:
            # 规范化路径，解析符号链接
            real_path = Path(file_path).resolve()
            allowed_dir = Path(self.uploads_dir).resolve()

            # 确保路径在允许的目录内
            return real_path.is_relative_to(allowed_dir)
        except Exception as e:
            logger.warning(f"路径验证失败: {file_path}, 错误: {e}")
            return False

    def create_backup(self, description: str = "手动备份", include_uploads: bool = True) -> BackupRecord:
        """
        创建系统备份

        Args:
            description: 备份描述
            include_uploads: 是否包含上传文件

        Returns:
            备份记录
        """
        # 生成备份文件名
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_file_name = f"backup_{timestamp}.zip"
        backup_file_path = os.path.join(self.backup_dir, backup_file_name)

        # 创建备份
        with zipfile.ZipFile(backup_file_path, "w", zipfile.ZIP_DEFLATED) as zipf:
            # 备份数据库
            if os.path.exists(self.database_path):
                zipf.write(self.database_path, "data/rural_revitalization.db")

            # 备份上传文件
            if include_uploads and os.path.exists(self.uploads_dir):
                for root, dirs, files in os.walk(self.uploads_dir):
                    for file in files:
                        file_path = os.path.join(root, file)

                        # 验证路径安全性，防止路径遍历攻击
                        if not self._validate_path(file_path):
                            logger.warning(f"跳过不安全的路径: {file_path}")
                            continue

                        arcname = os.path.join("uploads", os.path.relpath(file_path, self.uploads_dir))
                        zipf.write(file_path, arcname)

            # 添加备份信息
            backup_info = {
                "timestamp": timestamp,
                "description": description,
                "include_uploads": include_uploads,
                "database_included": os.path.exists(self.database_path),
                "created_at": datetime.now().isoformat(),
            }
            zipf.writestr("backup_info.json", str(backup_info))

        # 获取文件大小
        file_size = os.path.getsize(backup_file_path)

        # 保存备份记录到数据库
        config_key = f"backup_{timestamp}"
        config = SystemConfig(key=config_key, value=backup_file_path, description=f"备份: {description}")
        self.db.add(config)

        # 更新最后备份时间
        from app.services.system_config_service import SystemConfigService

        config_service = SystemConfigService(self.db)
        config_service.set("last_backup_time", datetime.now().isoformat())

        self.db.commit()

        return BackupRecord(
            backup_id=config.id,
            file_name=backup_file_name,
            file_path=backup_file_path,
            file_size=file_size,
            description=description,
            created_at=datetime.now(),
        )

    def _safe_extractall(self, zipf: zipfile.ZipFile, dest_dir: str) -> None:
        """
        安全解压 ZIP 文件，防止 zip slip 路径穿越攻击。

        对包内每个成员的目标路径进行规范化校验，确保最终路径仍在
        dest_dir 内部，否则跳过该成员并记录警告。
        """
        dest_path = Path(dest_dir).resolve()
        for member in zipf.infolist():
            # 规范化成员名称中的反斜杠（Windows zip 兼容）
            member_name = member.filename.replace("\\", "/")
            # 拒绝绝对路径或包含 ".." 的成员
            if os.path.isabs(member_name) or ".." in member_name.split("/"):
                logger.warning(f"跳过不安全的 zip 成员: {member.filename}")
                continue
            target = (dest_path / member_name).resolve()
            try:
                target.relative_to(dest_path)
            except ValueError:
                logger.warning(f"跳过逃逸路径的 zip 成员: {member.filename}")
                continue
            zipf.extract(member, dest_dir)

    def restore_backup(self, backup_file_path: str) -> Dict:
        """
        从备份恢复系统（带事务保护）

        Args:
            backup_file_path: 备份文件路径

        Returns:
            恢复结果
        """
        if not os.path.exists(backup_file_path):
            raise FileNotFoundError(f"备份文件不存在: {backup_file_path}")

        # 解压备份文件到临时目录
        temp_dir = tempfile.mkdtemp(prefix="restore_")

        # 保存当前状态的快照路径
        snapshot_db_path = None
        snapshot_uploads_dir = None

        try:
            # 创建当前数据库快照
            if os.path.exists(self.database_path):
                snapshot_db_path = f"{self.database_path}.snapshot_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
                shutil.copy(self.database_path, snapshot_db_path)

            # 创建上传文件快照
            if os.path.exists(self.uploads_dir):
                snapshot_uploads_dir = f"{self.uploads_dir}_snapshot_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
                shutil.copytree(self.uploads_dir, snapshot_uploads_dir)

            # 解压备份文件（使用安全解压，防止 zip slip）
            with zipfile.ZipFile(backup_file_path, "r") as zipf:
                self._safe_extractall(zipf, temp_dir)

            # 恢复数据库
            backup_db_path = os.path.join(temp_dir, "data/rural_revitalization.db")
            database_restored = False
            if os.path.exists(backup_db_path):
                os.makedirs(os.path.dirname(self.database_path), exist_ok=True)
                shutil.copy(backup_db_path, self.database_path)
                database_restored = True

            # 恢复上传文件
            backup_uploads_dir = os.path.join(temp_dir, "uploads")
            uploads_restored = False
            if os.path.exists(backup_uploads_dir):
                if os.path.exists(self.uploads_dir):
                    shutil.rmtree(self.uploads_dir, ignore_errors=True)
                shutil.copytree(backup_uploads_dir, self.uploads_dir)
                uploads_restored = True

            # 恢复成功，删除快照
            if snapshot_db_path and os.path.exists(snapshot_db_path):
                try:
                    os.unlink(snapshot_db_path)
                except FileNotFoundError:
                    pass
            if snapshot_uploads_dir and os.path.exists(snapshot_uploads_dir):
                shutil.rmtree(snapshot_uploads_dir, ignore_errors=True)

            return {
                "success": True,
                "message": "系统恢复成功",
                "database_restored": database_restored,
                "uploads_restored": uploads_restored,
            }

        except Exception as e:
            # 恢复失败，回滚到快照
            if snapshot_db_path and os.path.exists(snapshot_db_path):
                if os.path.exists(self.database_path):
                    try:
                        os.unlink(self.database_path)
                    except FileNotFoundError:
                        pass
                shutil.copy(snapshot_db_path, self.database_path)
                try:
                    os.unlink(snapshot_db_path)
                except FileNotFoundError:
                    pass

            if snapshot_uploads_dir and os.path.exists(snapshot_uploads_dir):
                if os.path.exists(self.uploads_dir):
                    shutil.rmtree(self.uploads_dir, ignore_errors=True)
                shutil.copytree(snapshot_uploads_dir, self.uploads_dir)
                shutil.rmtree(snapshot_uploads_dir, ignore_errors=True)

            raise BackupRestoreError(f"恢复失败，已回滚到原始状态: {e}")

        finally:
            # 清理临时文件
            if os.path.exists(temp_dir):
                shutil.rmtree(temp_dir, ignore_errors=True)

    def list_backups(self) -> List[BackupRecord]:
        """
        列出所有备份

        Returns:
            备份记录列表
        """
        backups = []

        # 查询数据库中的备份记录
        configs = (
            self.db.query(SystemConfig)
            .filter(SystemConfig.key.like("backup_%"))
            .order_by(SystemConfig.created_at.desc())
            .all()
        )

        for config in configs:
            if os.path.exists(config.value):
                file_size = os.path.getsize(config.value)
                file_name = os.path.basename(config.value)

                backups.append(
                    BackupRecord(
                        backup_id=config.id,
                        file_name=file_name,
                        file_path=config.value,
                        file_size=file_size,
                        description=config.description,
                        created_at=config.created_at,
                    )
                )

        return backups

    def delete_backup(self, backup_id: int) -> bool:
        """
        删除备份

        Args:
            backup_id: 备份ID

        Returns:
            是否删除成功
        """
        config = self.db.query(SystemConfig).filter(SystemConfig.id == backup_id).first()

        if not config:
            return False

        # 删除备份文件
        if os.path.exists(config.value):
            try:
                os.unlink(config.value)
            except FileNotFoundError:
                pass

        # 删除数据库记录
        self.db.delete(config)
        self.db.commit()

        return True

    def cleanup_old_backups(self, keep_count: int = 10) -> int:
        """
        清理旧备份

        Args:
            keep_count: 保留的备份数量

        Returns:
            删除的备份数量
        """
        # 获取所有备份
        configs = (
            self.db.query(SystemConfig)
            .filter(SystemConfig.key.like("backup_%"))
            .order_by(SystemConfig.created_at.desc())
            .all()
        )

        # 删除超出数量的旧备份
        deleted_count = 0
        for config in configs[keep_count:]:
            if os.path.exists(config.value):
                try:
                    os.unlink(config.value)
                except FileNotFoundError:
                    pass
            self.db.delete(config)
            deleted_count += 1

        if deleted_count > 0:
            self.db.commit()

        return deleted_count

    def get_backup_size(self) -> int:
        """
        获取备份目录总大小

        Returns:
            总大小（字节）
        """
        try:
            total_size = 0
            if not os.path.exists(self.backup_dir):
                logger.warning(f"备份目录不存在: {self.backup_dir}")
                return 0

            for file in os.listdir(self.backup_dir):
                file_path = os.path.join(self.backup_dir, file)
                if os.path.isfile(file_path):
                    total_size += os.path.getsize(file_path)
            return total_size
        except Exception as e:
            logger.error(f"计算备份大小失败: {e}")
            return 0

    # ==================== 增量备份功能 ====================

    def _load_last_manifest(self) -> Optional[Dict]:
        """加载最后一次备份的清单"""
        try:
            manifest_file = os.path.join(self.backup_dir, "last_manifest.json")
            if os.path.exists(manifest_file):
                with open(manifest_file, "r", encoding="utf-8") as f:
                    return json.load(f)
            return None
        except Exception as e:
            logger.error(f"加载备份清单失败: {e}")
            return None

    def _save_manifest(self, manifest: Dict):
        """保存备份清单"""
        try:
            manifest_file = os.path.join(self.backup_dir, "last_manifest.json")
            with open(manifest_file, "w", encoding="utf-8") as f:
                json.dump(manifest, f, indent=2, ensure_ascii=False)
        except Exception as e:
            logger.error(f"保存备份清单失败: {e}")

    def _calculate_file_hash(self, file_path: str) -> str:
        """计算文件SHA256哈希"""
        try:
            sha256 = hashlib.sha256()
            with open(file_path, "rb") as f:
                for chunk in iter(lambda: f.read(4096), b""):
                    sha256.update(chunk)
            return sha256.hexdigest()
        except Exception as e:
            logger.error(f"计算文件哈希失败 {file_path}: {e}")
            return ""

    def _get_file_manifest(self, directory: str) -> Dict[str, Dict]:
        """获取目录下所有文件的清单（路径 -> {size, mtime, hash}）"""
        manifest = {}
        try:
            if not os.path.exists(directory):
                return manifest

            for root, dirs, files in os.walk(directory):
                for file in files:
                    file_path = os.path.join(root, file)
                    if not self._validate_path(file_path):
                        continue

                    try:
                        stat = os.stat(file_path)
                        rel_path = os.path.relpath(file_path, ".")
                        manifest[rel_path] = {
                            "size": stat.st_size,
                            "mtime": stat.st_mtime,
                            "hash": self._calculate_file_hash(file_path),
                        }
                    except Exception as e:
                        logger.warning(f"获取文件信息失败 {file_path}: {e}")

            return manifest
        except Exception as e:
            logger.error(f"获取文件清单失败: {e}")
            return manifest

    def create_incremental_backup(self, description: str = "增量备份", include_uploads: bool = True) -> Dict:
        """
        创建增量备份（仅备份变更的文件）

        Args:
            description: 备份描述
            include_uploads: 是否包含上传文件

        Returns:
            备份结果
        """
        if not self.incremental_enabled:
            logger.warning("增量备份未启用，执行完整备份")
            result = self.create_backup(description, include_uploads)
            # 转换BackupRecord为Dict
            if result:
                return {
                    "status": "success",
                    "backup_id": result.backup_id,
                    "file_name": result.file_name,
                    "file_path": result.file_path,
                    "file_size": result.file_size,
                    "backup_type": "full",
                    "description": description,
                    "created_at": result.created_at.isoformat(),
                }
            else:
                return {"status": "error", "message": "创建完整备份失败"}

        logger.info("开始创建增量备份...")

        try:
            # 生成备份文件名
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            backup_file_name = f"backup_incremental_{timestamp}.zip"
            backup_file_path = os.path.join(self.backup_dir, backup_file_name)

            # 获取当前文件清单
            current_manifest = {}

            # 数据库文件
            if os.path.exists(self.database_path):
                current_manifest[self.database_path] = {
                    "size": os.path.getsize(self.database_path),
                    "mtime": os.path.getmtime(self.database_path),
                    "hash": self._calculate_file_hash(self.database_path),
                }

            # 上传文件
            if include_uploads:
                uploads_manifest = self._get_file_manifest(self.uploads_dir)
                current_manifest.update(uploads_manifest)

            # 比较清单，找出变更的文件
            changed_files = []
            if self.last_backup_manifest:
                for file_path, file_info in current_manifest.items():
                    last_info = self.last_backup_manifest.get(file_path)
                    if not last_info or last_info["hash"] != file_info["hash"]:
                        changed_files.append(file_path)
            else:
                # 没有上次备份，所有文件都是变更的
                changed_files = list(current_manifest.keys())

            if not changed_files:
                logger.info("没有文件变更，跳过增量备份")
                return {
                    "status": "skipped",
                    "message": "没有文件变更",
                    "changed_files": 0,
                }

            logger.info(f"发现 {len(changed_files)} 个变更文件")

            # 创建增量备份
            with zipfile.ZipFile(
                backup_file_path,
                "w",
                zipfile.ZIP_DEFLATED,
                compresslevel=self.compression_level,
            ) as zipf:
                for file_path in changed_files:
                    if os.path.exists(file_path):
                        # 使用相对路径作为 arcname，防止绝对路径写入 zip（zip slip 风险）
                        try:
                            arcname = os.path.relpath(file_path)
                        except ValueError:
                            # Windows 上跨盘符 relpath 会抛 ValueError，回退到文件名
                            arcname = os.path.basename(file_path)
                        zipf.write(file_path, arcname)

                # 添加备份信息
                backup_info = {
                    "timestamp": timestamp,
                    "description": description,
                    "backup_type": "incremental",
                    "include_uploads": include_uploads,
                    "changed_files": len(changed_files),
                    "created_at": datetime.now().isoformat(),
                    "manifest": current_manifest,
                }
                zipf.writestr(
                    "backup_info.json",
                    json.dumps(backup_info, indent=2, ensure_ascii=False),
                )

            # 保存清单
            self._save_manifest(current_manifest)
            self.last_backup_manifest = current_manifest

            # 获取文件大小
            file_size = os.path.getsize(backup_file_path)

            # 保存备份记录到数据库
            config_key = f"backup_incremental_{timestamp}"
            config = SystemConfig(
                key=config_key,
                value=backup_file_path,
                description=f"增量备份: {description} ({len(changed_files)}个文件)",
            )
            self.db.add(config)

            # 更新最后备份时间
            from app.services.system_config_service import SystemConfigService

            config_service = SystemConfigService(self.db)
            try:
                config_service.set("last_backup_time", datetime.now().isoformat())
            except Exception as e:
                # 如果key已存在，更新而不是插入
                logger.warning(f"更新last_backup_time失败，尝试更新: {e}")
                existing = self.db.query(SystemConfig).filter(SystemConfig.key == "last_backup_time").first()
                if existing:
                    existing.value = datetime.now().isoformat()
                    existing.updated_at = datetime.now()

            self.db.commit()

            logger.info(f"增量备份完成: {backup_file_name} ({file_size / 1024 / 1024:.2f}MB)")

            return {
                "status": "success",
                "backup_id": config.id,
                "file_name": backup_file_name,
                "file_path": backup_file_path,
                "file_size": file_size,
                "backup_type": "incremental",
                "changed_files": len(changed_files),
                "description": description,
                "created_at": datetime.now().isoformat(),
            }

        except Exception as e:
            error_msg = f"创建增量备份失败: {e}"
            logger.error(error_msg, exc_info=True)
            return {"status": "error", "message": error_msg}

    def verify_backup(self, backup_file_path: str) -> Dict:
        """
        验证备份文件完整性

        Args:
            backup_file_path: 备份文件路径

        Returns:
            验证结果
        """
        logger.info(f"验证备份文件: {backup_file_path}")

        try:
            if not os.path.exists(backup_file_path):
                return {"status": "error", "message": "备份文件不存在"}

            # 计算文件哈希
            file_hash = self._calculate_file_hash(backup_file_path)

            # 尝试打开ZIP文件
            with zipfile.ZipFile(backup_file_path, "r") as zipf:
                # 测试ZIP文件完整性
                bad_file = zipf.testzip()
                if bad_file:
                    return {
                        "status": "error",
                        "message": f"ZIP文件损坏: {bad_file}",
                    }

                # 读取备份信息
                try:
                    backup_info_data = zipf.read("backup_info.json")
                    backup_info = json.loads(backup_info_data)
                except Exception:
                    backup_info = None

                # 获取文件列表
                file_list = zipf.namelist()

            # 验证数据库文件（如果存在）
            db_verified = False
            if "data/rural_revitalization.db" in file_list:
                # 提取数据库文件到临时位置
                temp_dir = tempfile.mkdtemp(prefix="verify_")

                try:
                    with zipfile.ZipFile(backup_file_path, "r") as zipf:
                        zipf.extract("data/rural_revitalization.db", temp_dir)

                    temp_db_path = os.path.join(temp_dir, "data/rural_revitalization.db")

                    # 验证数据库完整性
                    conn = sqlite3.connect(temp_db_path)
                    cursor = conn.cursor()
                    cursor.execute("PRAGMA integrity_check")
                    result = cursor.fetchone()
                    conn.close()

                    db_verified = result and result[0] == "ok"

                finally:
                    # 清理临时文件
                    if os.path.exists(temp_dir):
                        shutil.rmtree(temp_dir, ignore_errors=True)

            return {
                "status": "ok",
                "message": "备份文件验证通过",
                "file_hash": file_hash,
                "file_count": len(file_list),
                "backup_info": backup_info,
                "database_verified": db_verified,
            }

        except Exception as e:
            error_msg = f"验证备份失败: {e}"
            logger.error(error_msg, exc_info=True)
            return {"status": "error", "message": error_msg}

    def get_backup_statistics(self) -> Dict:
        """获取备份统计信息"""
        try:
            backups = self.list_backups()

            total_size = sum(b.file_size for b in backups)
            full_backups = [b for b in backups if b.backup_type == "full"]
            incremental_backups = [b for b in backups if b.backup_type == "incremental"]

            return {
                "total_backups": len(backups),
                "full_backups": len(full_backups),
                "incremental_backups": len(incremental_backups),
                "total_size": total_size,
                "total_size_mb": round(total_size / 1024 / 1024, 2),
                "oldest_backup": (backups[-1].created_at.isoformat() if backups else None),
                "newest_backup": backups[0].created_at.isoformat() if backups else None,
            }

        except Exception as e:
            logger.error(f"获取备份统计失败: {e}")
            return {"status": "error", "message": str(e)}


def get_backup_service(db: Session = None) -> "BackupService":
    """
    获取备份服务实例。

    如果传入了 db session，则每次返回绑定该 session 的新实例（避免复用过期
    session）。仅当 db=None 且需要一个无 session 的轻量实例时，才使用全局
    缓存（仅用于读取备份目录等不涉及数据库写入的场景）。
    """
    if db is not None:
        return BackupService(db)

    # db=None 时才使用全局缓存（仅限只读场景，如 download/preview）
    global _backup_service_no_db
    if _backup_service_no_db is None:
        _backup_service_no_db = BackupService(None)
    return _backup_service_no_db


# 全局无 db 缓存实例（仅供只读路由使用，延迟初始化）
_backup_service_no_db = None

# 使用 get_backup_service() 获取服务实例（延迟初始化）
# 不要在这里直接实例化，以避免模块导入时的副作用
