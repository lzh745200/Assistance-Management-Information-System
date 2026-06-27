# -*- coding: utf-8 -*-
"""
机器码和校验码服务
用于单机版系统的用户认证和注册管理
"""

import hashlib
import logging
import platform
import secrets
import subprocess
import uuid
from datetime import datetime, timezone
from typing import Optional

from sqlalchemy import and_
from sqlalchemy.orm import Session

from app.models.machine_code import MachineCode

logger = logging.getLogger(__name__)


class MachineCodeService:
    """机器码服务

    提供机器码生成、管理和验证功能。
    """

    def __init__(self, db: Optional[Session] = None):
        """初始化机器码服务

        Args:
            db: 数据库会话（可选，用于数据库操作）
        """
        self.db = db

    # 进程级缓存：机器码在进程生命周期内不变，首次计算后缓存
    _cached_machine_code: Optional[str] = None

    @staticmethod
    def _collect_wmic_info() -> list:
        if platform.system() != "Windows":
            return []

        wmic_queries = [
            (["wmic", "cpu", "get", "ProcessorId"], None),
            (["wmic", "baseboard", "get", "SerialNumber"], "To be filled by O.E.M."),
            (["wmic", "diskdrive", "get", "SerialNumber"], None),
        ]
        procs = []
        for cmd, _ in wmic_queries:
            try:
                procs.append(
                    (
                        subprocess.Popen(
                            cmd,
                            stdout=subprocess.PIPE,
                            stderr=subprocess.DEVNULL,
                            text=True,
                            encoding="utf-8",
                            errors="ignore",
                            creationflags=0x08000000,
                        ),
                        _,
                    )
                )
            except Exception:
                procs.append((None, _))

        info = []
        for proc, skip_val in procs:
            if proc is None:
                continue
            try:
                stdout, _ = proc.communicate(timeout=2)
                val = stdout.strip().split("\n")[-1].strip()
                if val and val != skip_val:
                    info.append(val)
            except Exception:
                try:
                    proc.kill()
                except Exception:
                    logger.debug("终止机器信息采集进程失败")
        return info

    @staticmethod
    def _get_mac_address() -> Optional[str]:
        try:
            return ":".join(
                ["{:02x}".format((uuid.getnode() >> elements) & 0xFF) for elements in range(0, 2 * 6, 2)][::-1]
            )
        except Exception:
            logger.debug("获取 MAC 地址失败")
            return None

    @staticmethod
    def _get_computer_name() -> Optional[str]:
        try:
            name = platform.node()
            return name if name else None
        except Exception:
            logger.debug("获取计算机名失败")
            return None

    @staticmethod
    def get_machine_code() -> str:
        """
        获取当前机器的唯一标识码

        结果被进程级缓存，首次调用后后续调用直接返回，无需重复执行
        wmic 子进程（每次登录可节省数秒）。

        Returns:
            机器码（32位十六进制字符串）
        """
        if MachineCodeService._cached_machine_code is not None:
            return MachineCodeService._cached_machine_code

        machine_info = []
        machine_info.extend(MachineCodeService._collect_wmic_info())

        mac = MachineCodeService._get_mac_address()
        if mac:
            machine_info.append(mac)

        computer_name = MachineCodeService._get_computer_name()
        if computer_name:
            machine_info.append(computer_name)

        if not machine_info:
            machine_info.append(str(uuid.uuid4()))

        combined = "|".join(machine_info)
        machine_code = hashlib.sha256(combined.encode()).hexdigest()
        MachineCodeService._cached_machine_code = machine_code

        return machine_code

    @staticmethod
    def generate_verification_code(machine_code: str) -> str:
        """
        根据机器码生成4位数字校验码

        Args:
            machine_code: 机器码

        Returns:
            4位数字校验码
        """
        # 使用机器码的哈希值生成4位数字
        hash_value = hashlib.md5(machine_code.encode(), usedforsecurity=False).hexdigest()

        # 取哈希值的前8位，转换为整数
        num = int(hash_value[:8], 16)

        # 取模得到4位数字（1000-9999）
        verification_code = (num % 9000) + 1000

        return str(verification_code)

    @staticmethod
    def verify_machine_code(machine_code: str, verification_code: str) -> bool:
        """
        验证机器码和校验码是否匹配

        Args:
            machine_code: 机器码
            verification_code: 校验码

        Returns:
            是否匹配
        """
        expected_code = MachineCodeService.generate_verification_code(machine_code)
        return expected_code == verification_code

    @staticmethod
    def generate_initial_password(username: str, verification_code: str) -> str:
        """
        生成初始登录密码

        规则：用户名前4位 + 校验码 + 固定后缀
        例如：admin + 1234 + @RRS

        Args:
            username: 用户名
            verification_code: 校验码

        Returns:
            初始密码
        """
        # 取用户名前4位（不足4位则全取）
        username_prefix = username[:4].upper()

        # 组合密码
        password = f"{username_prefix}{verification_code}@RRS"

        return password

    @staticmethod
    def get_machine_info() -> dict:
        """
        获取机器详细信息（用于显示）

        Returns:
            机器信息字典
        """
        info = {
            "system": platform.system(),
            "release": platform.release(),
            "version": platform.version(),
            "machine": platform.machine(),
            "processor": platform.processor(),
            "node": platform.node(),
        }

        # Windows 特定信息
        if platform.system() == "Windows":
            try:
                # CPU 信息
                result = subprocess.run(
                    ["wmic", "cpu", "get", "Name"],
                    capture_output=True,
                    text=True,
                    encoding="utf-8",
                    errors="ignore",
                    timeout=5,
                )
                cpu_name = result.stdout.strip().split("\n")[-1].strip()
                info["cpu_name"] = cpu_name
            except Exception:
                logger.debug("获取 CPU 信息失败")

            try:
                # 内存信息
                result = subprocess.run(
                    ["wmic", "computersystem", "get", "TotalPhysicalMemory"],
                    capture_output=True,
                    text=True,
                    encoding="utf-8",
                    errors="ignore",
                    timeout=5,
                )
                memory = result.stdout.strip().split("\n")[-1].strip()
                if memory:
                    memory_gb = int(memory) / (1024**3)
                    info["memory_gb"] = round(memory_gb, 2)
            except Exception:
                logger.debug("获取内存信息失败")

        return info

    @staticmethod
    def generate_pass_code(machine_code: str) -> str:
        """为指定机器码生成通行码（激活码）

        通行码是基于机器码和随机盐生成的激活码。

        Args:
            machine_code: 机器码

        Returns:
            str: 通行码（格式化为 XXXX-XXXX-XXXX-XXXX-XXXX-XXXX-XXXX-XXXX）
        """
        # 生成随机盐
        salt = secrets.token_hex(16)

        # 组合机器码和盐生成通行码
        combined = f"{machine_code}:{salt}"
        pass_code = hashlib.sha256(combined.encode()).hexdigest()[:32]

        # 格式化为易读格式：XXXX-XXXX-XXXX-XXXX-XXXX-XXXX-XXXX-XXXX
        formatted = "-".join([pass_code[i: i + 4] for i in range(0, 32, 4)])

        return formatted

    def create_machine_code_record(
        self,
        machine_code: str,
        created_by: int,
        description: Optional[str] = None,
        pass_code: Optional[str] = None,
    ) -> MachineCode:
        """管理员录入机器码并生成通行码

        Args:
            machine_code: 用户提供的机器码
            created_by: 创建人ID（管理员）
            description: 备注说明
            pass_code: 手动设置的4位数字通行码（留空则自动生成32位通行码）

        Returns:
            MachineCode: 创建的机器码记录

        Raises:
            ValueError: 机器码已存在或数据库会话未初始化
        """
        if not self.db:
            raise ValueError("数据库会话未初始化")

        # 检查机器码是否已存在
        existing = self.db.query(MachineCode).filter(MachineCode.machine_code == machine_code).first()
        if existing:
            raise ValueError("该机器码已存在")

        # 如果提供了4位通行码则使用，否则自动生成32位通行码
        final_pass_code = pass_code if pass_code else self.generate_pass_code(machine_code)

        # 创建记录
        record = MachineCode(
            machine_code=machine_code,
            pass_code=final_pass_code,
            status="pending",
            created_by=created_by,
            description=description,
        )

        self.db.add(record)
        self.db.commit()
        self.db.refresh(record)

        logger.info(
            f"管理员创建机器码记录: machine_code={machine_code[:16]}..., "
            f"pass_code={final_pass_code[:16] if final_pass_code else 'None'}..., created_by={created_by}"
        )

        return record

    def verify_pass_code(self, pass_code: str, machine_code: str) -> Optional[MachineCode]:
        """验证通行码是否有效

        Args:
            pass_code: 用户输入的通行码
            machine_code: 当前机器的机器码

        Returns:
            Optional[MachineCode]: 验证通过返回机器码记录，否则返回None

        Raises:
            ValueError: 数据库会话未初始化
        """
        if not self.db:
            raise ValueError("数据库会话未初始化")

        # 查询通行码记录
        record = (
            self.db.query(MachineCode)
            .filter(
                and_(
                    MachineCode.pass_code == pass_code,
                    MachineCode.machine_code == machine_code,
                    MachineCode.status == "pending",
                )
            )
            .first()
        )

        if not record:
            logger.warning(f"通行码验证失败: pass_code={pass_code[:16]}..., " f"machine_code={machine_code[:16]}...")
            return None

        logger.info(f"通行码验证成功: pass_code={pass_code[:16]}...")
        return record

    def activate_machine_code(self, record: MachineCode, user_id: int) -> None:
        """激活机器码（绑定到用户）

        Args:
            record: 机器码记录
            user_id: 用户ID

        Raises:
            ValueError: 数据库会话未初始化
        """
        if not self.db:
            raise ValueError("数据库会话未初始化")

        record.status = "active"
        record.user_id = user_id
        record.activated_at = datetime.now(timezone.utc)

        self.db.commit()

        logger.info(f"机器码已激活: machine_code={record.machine_code[:16]}..., " f"user_id={user_id}")

    def revoke_machine_code(self, machine_code_id: int) -> bool:
        """撤销机器码

        Args:
            machine_code_id: 机器码记录ID

        Returns:
            bool: 是否成功撤销

        Raises:
            ValueError: 数据库会话未初始化
        """
        if not self.db:
            raise ValueError("数据库会话未初始化")

        record = self.db.query(MachineCode).filter(MachineCode.id == machine_code_id).first()
        if not record:
            return False

        record.status = "revoked"
        record.revoked_at = datetime.now(timezone.utc)

        self.db.commit()

        logger.info(f"机器码已撤销: id={machine_code_id}, machine_code={record.machine_code[:16]}...")
        return True

    def get_machine_code_by_user(self, user_id: int) -> Optional[MachineCode]:
        """获取用户绑定的机器码

        Args:
            user_id: 用户ID

        Returns:
            Optional[MachineCode]: 机器码记录

        Raises:
            ValueError: 数据库会话未初始化
        """
        if not self.db:
            raise ValueError("数据库会话未初始化")

        return (
            self.db.query(MachineCode)
            .filter(
                and_(
                    MachineCode.user_id == user_id,
                    MachineCode.status == "active",
                )
            )
            .first()
        )

    def verify_user_machine(self, user_id: int, current_machine_code: str) -> bool:
        """验证用户是否在授权的机器上登录

        Args:
            user_id: 用户ID
            current_machine_code: 当前机器的机器码

        Returns:
            bool: 是否授权

        Raises:
            ValueError: 数据库会话未初始化
        """
        if not self.db:
            raise ValueError("数据库会话未初始化")

        record = self.get_machine_code_by_user(user_id)
        if not record:
            # 用户未绑定机器码，允许登录（兼容旧用户）
            logger.info(f"用户未绑定机器码，允许登录: user_id={user_id}")
            return True

        is_authorized = record.machine_code == current_machine_code
        if not is_authorized:
            logger.warning(
                f"用户尝试在未授权的机器上登录: user_id={user_id}, "
                f"expected={record.machine_code[:16]}..., "
                f"actual={current_machine_code[:16]}..."
            )

        return is_authorized

    def list_machine_codes(
        self,
        status: Optional[str] = None,
        skip: int = 0,
        limit: int = 100,
    ) -> tuple[list[MachineCode], int]:
        """查询机器码列表

        Args:
            status: 状态筛选（pending/active/revoked）
            skip: 跳过记录数
            limit: 返回记录数

        Returns:
            tuple[list[MachineCode], int]: (机器码列表, 总数)

        Raises:
            ValueError: 数据库会话未初始化
        """
        if not self.db:
            raise ValueError("数据库会话未初始化")

        query = self.db.query(MachineCode)

        if status:
            query = query.filter(MachineCode.status == status)

        total = query.count()

        # 使用 joinedload 预加载用户关系，避免 N+1 查询
        from sqlalchemy.orm import joinedload

        records = (
            query.options(joinedload(MachineCode.user))
            .order_by(MachineCode.created_at.desc())
            .offset(skip)
            .limit(limit)
            .all()
        )

        return records, total

    # ==================== 组织通行证码相关方法 ====================

    @staticmethod
    def generate_organization_verification_code(organization_id: int, organization_name: str) -> str:
        """基于组织信息生成4位校验码（确定性）

        同一组织每次生成相同的校验码，便于验证和管理。

        Args:
            organization_id: 组织ID
            organization_name: 组织名称

        Returns:
            str: 4位数字校验码
        """
        # 组合组织ID和名称
        combined = f"{organization_id}:{organization_name}"

        # 使用 MD5 哈希
        hash_value = hashlib.md5(combined.encode(), usedforsecurity=False).hexdigest()

        # 取哈希值的前8位，转换为整数
        num = int(hash_value[:8], 16)

        # 取模得到4位数字（1000-9999）
        verification_code = (num % 9000) + 1000

        return str(verification_code)

    @staticmethod
    def generate_organization_pass_code(organization_id: int, verification_code: str) -> str:
        """生成12位组织通行码

        格式：XXXX-XXXX-XXXX（带连字符显示）

        Args:
            organization_id: 组织ID
            verification_code: 校验码

        Returns:
            str: 12位通行码（格式化为 XXXX-XXXX-XXXX）
        """
        # 生成随机盐
        salt = secrets.token_hex(8)

        # 组合组织ID、校验码和盐生成通行码
        combined = f"{organization_id}:{verification_code}:{salt}"

        # 使用 SHA256 哈希
        hash_value = hashlib.sha256(combined.encode()).hexdigest()

        # 取前12位字符（大写字母和数字）
        pass_code = hash_value[:12].upper()

        # 格式化为 XXXX-XXXX-XXXX
        formatted = f"{pass_code[:4]}-{pass_code[4:8]}-{pass_code[8:12]}"

        return formatted

    def create_organization_pass_code(
        self,
        organization_id: int,
        verification_code: str,
        allow_subordinate: bool,
        created_by: int,
        description: Optional[str] = None,
    ) -> MachineCode:
        """创建组织通行码记录

        Args:
            organization_id: 组织ID
            verification_code: 校验码
            allow_subordinate: 是否允许下级组织生成通行码
            created_by: 创建人ID
            description: 备注说明

        Returns:
            MachineCode: 创建的通行码记录

        Raises:
            ValueError: 数据库会话未初始化
        """
        if not self.db:
            raise ValueError("数据库会话未初始化")

        # 生成通行码
        pass_code = self.generate_organization_pass_code(organization_id, verification_code)

        # 生成一个虚拟的机器码（用于标识这是组织通行码）
        machine_code = f"ORG-{organization_id}-{secrets.token_hex(8)}"

        # 创建记录
        record = MachineCode(
            machine_code=machine_code,
            pass_code=pass_code,
            status="pending",
            organization_id=organization_id,
            allow_subordinate_generation=allow_subordinate,
            description=description,
            created_by=created_by,
        )

        self.db.add(record)
        self.db.commit()
        self.db.refresh(record)

        logger.info(
            f"组织通行码已创建: organization_id={organization_id}, "
            f"pass_code={pass_code}, allow_subordinate={allow_subordinate}"
        )

        return record

    def get_organization_pass_codes(
        self,
        organization_id: Optional[int] = None,
        status: Optional[str] = None,
        skip: int = 0,
        limit: int = 100,
    ) -> tuple[list[MachineCode], int]:
        """查询组织通行码列表

        Args:
            organization_id: 组织ID筛选（可选）
            status: 状态筛选（pending/active/revoked）
            skip: 跳过记录数
            limit: 返回记录数

        Returns:
            tuple[list[MachineCode], int]: (通行码列表, 总数)

        Raises:
            ValueError: 数据库会话未初始化
        """
        if not self.db:
            raise ValueError("数据库会话未初始化")

        # 查询组织通行码（organization_id 不为空）
        query = self.db.query(MachineCode).filter(MachineCode.organization_id.isnot(None))

        if organization_id:
            query = query.filter(MachineCode.organization_id == organization_id)

        if status:
            query = query.filter(MachineCode.status == status)

        total = query.count()

        # 使用 joinedload 预加载组织关系，避免 N+1 查询
        from sqlalchemy.orm import joinedload

        records = (
            query.options(joinedload(MachineCode.organization))
            .order_by(MachineCode.created_at.desc())
            .offset(skip)
            .limit(limit)
            .all()
        )

        return records, total


# 创建全局实例（用于静态方法调用）
machine_code_service = MachineCodeService()
