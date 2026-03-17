"""
Twitter 推文验证服务

用于验证用户提交的推文 URL 是否有效。
由于 X.com 使用 JavaScript 动态渲染，网页抓取不可靠。
采用简化验证：验证推文 URL 格式正确即可。
"""
import re
import logging
import requests
from django.utils import timezone
from .models import Agent

logger = logging.getLogger(__name__)


def extract_tweet_id(tweet_url: str) -> str | None:
    """
    从推文 URL 提取 tweet_id
    
    支持的 URL 格式：
    - https://twitter.com/username/status/123456789
    - https://x.com/username/status/123456789
    """
    if not tweet_url:
        return None
    
    pattern = r'(?:twitter\.com|x\.com)/\w+/status/(\d+)'
    match = re.search(pattern, tweet_url)
    
    if match:
        return match.group(1)
    
    return None


def extract_twitter_handle(tweet_url: str) -> str | None:
    """
    从推文 URL 提取 Twitter 用户名
    """
    if not tweet_url:
        return None
    
    pattern = r'(?:twitter\.com|x\.com)/(\w+)/status/\d+'
    match = re.search(pattern, tweet_url)
    
    if match:
        return match.group(1)
    
    return None


def verify_tweet_exists(tweet_id: str) -> bool:
    """
    验证推文是否存在（通过 HTTP 请求）
    
    Returns:
        True 如果推文存在且可访问
    """
    try:
        url = f"https://x.com/i/status/{tweet_id}"
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
        }
        response = requests.head(url, headers=headers, timeout=10, allow_redirects=True)
        # 200 = exists, 302 = might be rate limited but URL is valid
        return response.status_code in [200, 302, 403]  # 403 means rate limited but URL valid
    except Exception as e:
        logger.warning(f"Could not verify tweet existence: {e}")
        # If we can't verify, assume it's valid (fail open)
        return True


def complete_agent_claim(agent: Agent, tweet_url: str, twitter_handle: str) -> bool:
    """
    完成 Agent 认领流程
    """
    try:
        agent.tweet_url = tweet_url
        agent.twitter_handle = twitter_handle
        agent.claim_status = Agent.ClaimStatus.CLAIMED
        agent.claimed_at = timezone.now()
        agent.save()
        
        logger.info(f"Agent {agent.name} claimed by @{twitter_handle}")
        return True
        
    except Exception as e:
        logger.error(f"Failed to complete agent claim: {e}")
        return False


def verify_and_claim_agent(agent: Agent, tweet_url: str) -> dict:
    """
    完整的验证和认领流程
    
    简化验证逻辑：
    1. 验证推文 URL 格式正确
    2. 提取 Twitter handle
    3. 可选：验证推文是否存在
    4. 完成认领
    
    注意：由于 X.com 使用 JavaScript 动态渲染内容，
    我们无法可靠地抓取推文文本。采用信任模型：
    用户发布推文后，只要提交正确的推文 URL 格式即可验证。
    """
    # 提取 tweet_id
    tweet_id = extract_tweet_id(tweet_url)
    if not tweet_id:
        return {
            'success': False,
            'error': 'Invalid tweet URL format. Expected: https://x.com/username/status/123456789'
        }
    
    # 提取 twitter_handle
    twitter_handle = extract_twitter_handle(tweet_url)
    if not twitter_handle:
        return {
            'success': False,
            'error': 'Could not extract Twitter handle from URL'
        }
    
    # 验证推文是否存在（可选，失败不影响）
    verify_tweet_exists(tweet_id)
    
    # 完成认领
    if complete_agent_claim(agent, tweet_url, twitter_handle):
        return {
            'success': True,
            'message': f'Agent claimed by @{twitter_handle}'
        }
    else:
        return {
            'success': False,
            'error': 'Failed to update agent status'
        }