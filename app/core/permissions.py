"""
权限验证装饰器模块
"""

from functools import wraps
from typing import Callable, Optional

from app.core.exceptions import AppError
from app.models.user_model import User


def require_admin(func: Callable) -> Callable:
    """
    需要管理员权限的装饰器
    
    Args:
        func: 被装饰的函数
        
    Returns:
        装饰后的函数
        
    Raises:
        AppError: 当用户不是管理员时抛出权限错误
    """
    @wraps(func)
    async def wrapper(*args, **kwargs):
        # 从kwargs中获取current_user参数
        current_user: Optional[User] = kwargs.get('current_user')
        
        if not current_user:
            raise AppError("用户未登录")
            
        if current_user.user_type != 1:
            raise AppError("需要管理员权限")
            
        return await func(*args, **kwargs)
    return wrapper


def require_self_or_admin(func: Callable) -> Callable:
    """
    需要本人或管理员权限的装饰器
    
    Args:
        func: 被装饰的函数
        
    Returns:
        装饰后的函数
        
    Raises:
        AppError: 当用户没有权限时抛出权限错误
    """
    @wraps(func)
    async def wrapper(*args, **kwargs):
        # 从kwargs中获取参数
        current_user: Optional[User] = kwargs.get('current_user')
        target_user_id = kwargs.get('user_id')
        
        if not current_user:
            raise AppError("用户未登录")
            
        # 如果是管理员，允许操作
        if current_user.user_type == 1:
            return await func(*args, **kwargs)
            
        # 如果是普通用户，只能操作自己的资源
        if current_user.user_id != target_user_id:
            raise AppError("没有权限操作该用户")
            
        return await func(*args, **kwargs)
    return wrapper


def can_operate_user(current_user: User, target_user: User, operation: str) -> bool:
    """
    检查当前用户是否可以对目标用户执行指定操作
    
    Args:
        current_user: 当前操作用户
        target_user: 目标用户
        operation: 操作类型 ('delete', 'view', 'update')
        
    Returns:
        bool: 是否有权限执行操作
        
    Raises:
        AppError: 当没有权限时抛出权限错误
    """
    # 管理员可以执行所有操作
    if current_user.user_type == 1:
        # 但是不能删除自己
        if operation == 'delete' and current_user.user_id == target_user.user_id:
            raise AppError("不能删除自己的账户")
        return True
    
    # 普通用户的权限限制
    if operation == 'delete':
        raise AppError("普通用户不能删除用户")
        
    if operation == 'view':
        if current_user.user_id != target_user.user_id:
            raise AppError("没有权限查看该用户信息")
        return True
        
    if operation == 'update':
        # 普通用户不能修改管理员用户
        if target_user.user_type == 1:
            raise AppError("没有权限修改管理员用户")
            
        # 只能修改自己的信息
        if current_user.user_id != target_user.user_id:
            raise AppError("没有权限修改该用户信息")
        return True
        
    return False
