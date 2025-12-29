from sqlalchemy import Column, Integer, String, DateTime, Text, Index
from sqlalchemy.sql import func
from app.db.session import Base


class SysLog(Base):
    """
    系统日志数据库模型
    """

    __tablename__ = "sys_log"
    
    __table_args__ = (
        Index('idx_request_time', 'request_time'),           # 请求时间索引
        Index('idx_visit_module', 'visit_module'),           # 访问模块索引
        Index('idx_operation_status', 'operation_status'),    # 操作状态索引
    )

    id = Column(Integer, primary_key=True, autoincrement=True, comment="日志ID")
    request_url = Column(String(500), nullable=False, comment="请求接口URL")
    request_method = Column(String(10), nullable=False, comment="请求方法(GET/POST/PUT/DELETE)")
    request_params = Column(Text, comment="请求参数(JSON格式)")
    visit_module = Column(String(50), comment="访问模块")
    operation_type = Column(String(50), comment="操作类型")
    operation_status = Column(String(20), nullable=False, comment="操作结果(success/failure)")
    response_result = Column(Text, comment="返回结果(JSON格式)")
    request_time = Column(DateTime(timezone=True), nullable=False, comment="请求时间")
    duration = Column(Integer, comment="耗时(毫秒)")
    user_info = Column(String(500), comment="用户信息(JSON格式)")
    client_ip = Column(String(50), comment="客户端IP")
    user_agent = Column(String(500), comment="客户端User-Agent")
    created_at = Column(
        DateTime(timezone=True), server_default=func.now(), comment="创建时间"
    )