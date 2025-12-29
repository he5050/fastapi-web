from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from app.db.session import get_db, check_db_connection
from app.core.config import settings
from app.core.response import BaseResponse
from fastapi.responses import JSONResponse
from datetime import datetime

router = APIRouter(prefix="/health", tags=["系统监控"])


@router.get("", summary="系统健康检查")
async def health_check():
    """
    检查系统健康状态
    返回服务状态、数据库连接、版本信息等
    """
    health_status = {
        "status": "healthy",
        "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "app_name": settings.APP_NAME,
        "app_version": "1.0.0",
        "environment": settings.APP_ENV,
        "checks": {
            "database": "connected",
            "app": "running"
        }
    }
    
    # 检查数据库连接
    try:
        await check_db_connection()
        health_status["checks"]["database"] = "connected"
    except Exception as e:
        health_status["status"] = "unhealthy"
        health_status["checks"]["database"] = f"disconnected: {str(e)}"
    
    # 根据状态返回不同的HTTP状态码
    status_code = 200 if health_status["status"] == "healthy" else 503
    
    return JSONResponse(content=health_status, status_code=status_code)