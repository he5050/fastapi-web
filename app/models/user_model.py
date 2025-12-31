from sqlalchemy import Boolean, Column, DateTime, Index, Integer, String
from sqlalchemy.sql import func

from app.db.session import Base


class User(Base):
    """
    用户数据库模型
    """

    __tablename__ = "sys_users"

    __table_args__ = (
        Index("idx_user_name_email", "user_name", "email"),  # 复合索引
        Index("idx_created_at", "created_at"),  # 时间索引
    )

    user_id = Column(
        Integer, primary_key=True, index=True, autoincrement=True, comment="用户ID"
    )
    user_name = Column(
        String(50), unique=True, index=True, nullable=False, comment="用户名"
    )
    email = Column(String(100), unique=True, index=True, nullable=True, comment="邮箱")
    hashed_password = Column(String(255), nullable=False, comment="加密后的密码")
    full_name = Column(String(100), nullable=True, comment="全名")
    is_active = Column(Boolean, default=True, comment="是否激活")
    is_deleted = Column(Boolean, default=False, comment="是否已删除")
    user_type = Column(
        Integer,
        default=9,
        nullable=False,
        comment="用户类型：1-超级管理员，9-普通用户",
    )
    created_at = Column(
        DateTime(timezone=True), server_default=func.now(), comment="创建时间"
    )
    updated_at = Column(
        DateTime(timezone=True),
        onupdate=func.now(),
        server_default=func.now(),
        comment="更新时间",
    )
