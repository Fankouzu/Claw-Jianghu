from datetime import datetime, timedelta
from django.core.cache import cache
from typing import Tuple

def check_rate_limit(
    ip_address: str,
    action: str = 'login_request',
    limit: int = 5,
    window: int = 3600
) -> Tuple[bool, int, datetime]:
    """
    检查 IP 速率限制
    
    Args:
        ip_address: 客户端 IP 地址
        action: 操作类型（用于区分不同操作的计数）
        limit: 时间窗口内允许的最大请求数
        window: 时间窗口（秒）
    
    Returns:
        (allowed, remaining, reset_at):
        - allowed: 是否允许请求
        - remaining: 剩余请求次数
        - reset_at: 计数重置时间
    """
    cache_key = f"ratelimit:{action}:{ip_address}"
    current_count = cache.get(cache_key, 0)
    
    if current_count >= limit:
        # 尝试获取剩余过期时间，如果 cache 不支持 ttl 则默认使用 window
        ttl = getattr(cache, 'ttl', lambda x: window)(cache_key)
        if ttl is None or ttl <= 0:
            ttl = window
        reset_at = datetime.now() + timedelta(seconds=ttl)
        return (False, 0, reset_at)
    
    # 增加计数
    # 注意：Django 的 cache.set 会覆盖旧值，这里简单实现
    # 如果是 Redis，可以使用 cache.incr，但为了通用性使用 get/set
    new_count = current_count + 1
    cache.set(cache_key, new_count, window)
    
    remaining = limit - new_count
    reset_at = datetime.now() + timedelta(seconds=window)
    
    return (True, remaining, reset_at)

def reset_rate_limit(ip_address: str, action: str = 'login_request') -> None:
    """重置指定 IP 的速率限制计数"""
    cache_key = f"ratelimit:{action}:{ip_address}"
    cache.delete(cache_key)
