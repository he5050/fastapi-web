"""
Redis服务：管理JWT token存储和单点登录
"""
import json
from typing import Optional

from redis import Redis
from app.core.config import settings


class RedisService:
    """
    Redis服务类，用于管理token和单点登录
    """
    
    def __init__(self):
        """初始化Redis连接"""
        self._redis: Optional[Redis] = None
    
    def get_redis(self) -> Redis:
        """获取Redis连接（懒加载）"""
        if self._redis is None:
            redis_url = f"redis://:{settings.REDIS_PASSWORD}@{settings.REDIS_HOST}:{settings.REDIS_PORT}/{settings.REDIS_DB}"
            self._redis = Redis.from_url(
                redis_url,
                decode_responses=True,
                socket_timeout=settings.REDIS_TIMEOUT,
                socket_connect_timeout=settings.REDIS_TIMEOUT,
            )
        return self._redis
    
    def store_access_token(
        self,
        user_id: int,
        access_token: str,
        expires_in: int
    ) -> None:
        """
        存储访问token
        
        Args:
            user_id: 用户ID
            access_token: 访问token
            expires_in: 过期时间（秒）
        """
        redis = self.get_redis()
        
        # 生成token的key
        token_key = f"access_token:{access_token}"
        
        # 存储token与用户的映射
        redis.setex(
            token_key,
            expires_in,
            str(user_id)
        )
        
        # 将token添加到用户的token列表（用于单点登录）
        user_tokens_key = f"user_tokens:{user_id}"
        redis.lpush(user_tokens_key, access_token)
        # 设置过期时间为刷新token的过期时间（天转为秒）
        refresh_expire = settings.REFRESH_TOKEN_EXPIRE_DAYS * 24 * 60 * 60
        redis.expire(user_tokens_key, refresh_expire)
    
    def store_refresh_token(
        self,
        user_id: int,
        refresh_token: str
    ) -> None:
        """
        存储刷新token
        
        Args:
            user_id: 用户ID
            refresh_token: 刷新token
        """
        redis = self.get_redis()
        
        # 生成token的key
        token_key = f"refresh_token:{refresh_token}"
        
        # 存储token与用户的映射
        expires_in = settings.REFRESH_TOKEN_EXPIRE_DAYS * 24 * 60 * 60
        redis.setex(
            token_key,
            expires_in,
            str(user_id)
        )
    
    def get_user_id_by_access_token(self, access_token: str) -> Optional[int]:
        """
        通过访问token获取用户ID
        
        Args:
            access_token: 访问token
            
        Returns:
            用户ID，如果token不存在返回None
        """
        redis = self.get_redis()
        token_key = f"access_token:{access_token}"
        user_id_str = redis.get(token_key)
        
        return int(user_id_str) if user_id_str else None
    
    def get_user_id_by_refresh_token(self, refresh_token: str) -> Optional[int]:
        """
        通过刷新token获取用户ID
        
        Args:
            refresh_token: 刷新token
            
        Returns:
            用户ID，如果token不存在返回None
        """
        redis = self.get_redis()
        token_key = f"refresh_token:{refresh_token}"
        user_id_str = redis.get(token_key)
        
        return int(user_id_str) if user_id_str else None
    
    def revoke_access_token(self, access_token: str) -> None:
        """
        撤销访问token
        
        Args:
            access_token: 访问token
        """
        redis = self.get_redis()
        token_key = f"access_token:{access_token}"
        redis.delete(token_key)
    
    def revoke_refresh_token(self, refresh_token: str) -> None:
        """
        撤销刷新token
        
        Args:
            refresh_token: 刷新token
        """
        redis = self.get_redis()
        token_key = f"refresh_token:{refresh_token}"
        redis.delete(token_key)
    
    def revoke_all_user_tokens(self, user_id: int) -> None:
        """
        撤销用户的所有token（实现单点登录）
        
        当用户重新登录时，撤销其之前的所有token
        
        Args:
            user_id: 用户ID
        """
        redis = self.get_redis()
        user_tokens_key = f"user_tokens:{user_id}"
        
        # 获取用户的所有access token
        tokens = redis.lrange(user_tokens_key, 0, -1)
        
        # 删除所有access token
        for token in tokens:
            token_key = f"access_token:{token}"
            redis.delete(token_key)
        
        # 清空用户的token列表
        redis.delete(user_tokens_key)
    
    def validate_access_token(self, access_token: str) -> bool:
        """
        验证访问token是否有效
        
        Args:
            access_token: 访问token
            
        Returns:
            True表示token有效，False表示无效
        """
        redis = self.get_redis()
        token_key = f"access_token:{access_token}"
        return redis.exists(token_key) > 0
    
    def validate_refresh_token(self, refresh_token: str) -> bool:
        """
        验证刷新token是否有效
        
        Args:
            refresh_token: 刷新token
            
        Returns:
            True表示token有效，False表示无效
        """
        redis = self.get_redis()
        token_key = f"refresh_token:{refresh_token}"
        return redis.exists(token_key) > 0


# 全局单例
redis_service = RedisService()