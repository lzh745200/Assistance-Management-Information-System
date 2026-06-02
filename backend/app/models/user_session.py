"""
用户会话模型
支持多设备同时登录
"""

from sqlalchemy import Boolean, Column, DateTime, ForeignKey, Index, Integer, String
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from app.models.base import Base


class UserSession(Base):
    """用户会话表"""

    __tablename__ = "user_sessions"

    __table_args__ = (
        Index("ix_user_sessions_user_id", "user_id"),
        Index("ix_user_sessions_token", "token"),
        Index("ix_user_sessions_is_active", "is_active"),
        Index("ix_user_sessions_last_activity", "last_activity"),
    )

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(
        Integer,
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        comment="用户ID",
    )
    token = Column(String(500), unique=True, nullable=False, comment="会话令牌")
    device_info = Column(String(200), comment="设备信息")
    ip_address = Column(String(50), comment="IP地址")
    user_agent = Column(String(500), comment="用户代理")
    login_time = Column(DateTime(timezone=True), server_default=func.now(), comment="登录时间")
    last_activity = Column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        comment="最后活动时间",
    )
    is_active = Column(Boolean, default=True, comment="是否活跃")
    logout_time = Column(DateTime(timezone=True), nullable=True, comment="登出时间")

    # 关系
    user = relationship("User", backref="sessions")

    def __repr__(self):
        return f"<UserSession(id={self.id}, user_id={self.user_id}, is_active={self.is_active})>"
