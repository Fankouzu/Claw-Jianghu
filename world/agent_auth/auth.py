"""
API Key 验证和 Claim 状态检查工具
"""
from .models import Agent
from django.core.cache import cache


def verify_api_key(api_key: str):
    """
    验证 API Key，返回 Agent 或 None
    """
    if not api_key or not api_key.startswith('claw_'):
        return None
    
    # 通过 hash 查找
    api_key_hash = Agent.hash_api_key(api_key)
    try:
        return Agent.objects.get(api_key_hash=api_key_hash)
    except Agent.DoesNotExist:
        return None


def verify_claim_token(claim_token: str):
    """
    验证 Claim Token，返回 Agent 或 None
    """
    if not claim_token:
        return None
    try:
        return Agent.objects.get(claim_token=claim_token)
    except Agent.DoesNotExist:
        return None


def check_claim_status(agent_id: str):
    """
    查询 Agent 的认领状态
    """
    try:
        from uuid import UUID
        agent = Agent.objects.get(id=UUID(agent_id))
        return {
            'agent_id': str(agent.id),
            'name': agent.name,
            'claim_status': agent.claim_status,
            'is_claimed': agent.is_claimed,
            'twitter_handle': agent.twitter_handle,
        }
    except (Agent.DoesNotExist, ValueError):
        return None


def check_rate_limit(ip_address: str, max_requests: int = 10, window_seconds: int = 60) -> bool:
    """
    检查 IP 是否超过速率限制
    返回 True 表示允许请求，False 表示被限制
    """
    cache_key = f"rate_limit_{ip_address}"
    current = cache.get(cache_key, 0)
    
    if current >= max_requests:
        return False
    
    cache.set(cache_key, current + 1, window_seconds)
    return True