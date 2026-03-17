"""
Agent Claim 页面视图
"""
from django.shortcuts import render
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
from django.utils import timezone
import json
from .models import Agent, InvitationCode, UserEmail, EmailToken
from datetime import datetime
from .auth import verify_claim_token
from .twitter_verify import verify_and_claim_agent


# ============================================================================
# API 视图
# ============================================================================

@csrf_exempt
@require_http_methods(["GET"])
def agent_profile_api(request, agent_id):
    """
    GET /api/agents/{agent_id}/profile
    获取 Agent 档案信息 (API)
    """
    try:
        from uuid import UUID
        agent = Agent.objects.get(id=UUID(agent_id))
        
        return JsonResponse({
            'agent_id': str(agent.id),
            'name': agent.name,
            'level': agent.level,
            'experience': agent.experience,
            'claim_status': agent.claim_status,
            'twitter_handle': agent.twitter_handle,
            'created_at': agent.created_at.isoformat(),
            'last_active_at': agent.last_active_at.isoformat() if agent.last_active_at else None,
        })
    except (Agent.DoesNotExist, ValueError):
        return JsonResponse({'error': 'Agent not found'}, status=404)


@csrf_exempt
@require_http_methods(["POST"])
def agent_gain_experience(request, agent_id):
    """
    POST /api/agents/{agent_id}/experience
    增加 Agent 经验值（游戏内部调用）
    """
    try:
        from uuid import UUID
        import json
        
        agent = Agent.objects.get(id=UUID(agent_id))
        
        data = json.loads(request.body)
        exp_gain = data.get('experience', 0)
        
        if exp_gain <= 0:
            return JsonResponse({'error': 'experience must be positive'}, status=400)
        
        agent.experience += exp_gain
        
        # 简单的升级逻辑（每 100 经验升一级）
        new_level = agent.experience // 100 + 1
        if new_level > agent.level:
            agent.level = new_level
        
        agent.save()
        
        return JsonResponse({
            'agent_id': str(agent.id),
            'level': agent.level,
            'experience': agent.experience,
            'level_up': new_level > agent.level - (agent.experience - exp_gain) // 100
        })
        
    except (Agent.DoesNotExist, ValueError):
        return JsonResponse({'error': 'Agent not found'}, status=404)
    except json.JSONDecodeError:
        return JsonResponse({'error': 'Invalid JSON'}, status=400)


@csrf_exempt
@require_http_methods(["POST"])
def register_agent(request):
    """
    POST /api/agents/register
    注册新 Agent，返回 API Key 和 Claim URL
    
    需要 invitation_code 参数（邀请码）
    """
    try:
        data = json.loads(request.body)
        name = data.get('name', '').strip()
        description = data.get('description', '')
        invitation_code = data.get('invitation_code', '').strip().upper()
        
        if not name:
            return JsonResponse({'error': 'name is required'}, status=400)
        
        if not invitation_code:
            return JsonResponse({'error': 'invitation_code is required'}, status=400)
        
        # 验证邀请码
        try:
            inv_code = InvitationCode.objects.get(code=invitation_code)
        except InvitationCode.DoesNotExist:
            return JsonResponse({'error': 'Invalid invitation code'}, status=400)
        
        if inv_code.is_used:
            return JsonResponse({'error': 'Invitation code already used'}, status=400)
        
        # 检查名称是否已存在
        if Agent.objects.filter(name=name).exists():
            return JsonResponse({'error': 'Agent name already exists'}, status=409)
        
        # 创建 Agent
        agent, api_key = Agent.create_agent(name=name, description=description)
        
        # 标记邀请码为已使用
        inv_code.mark_used(agent)
        
        return JsonResponse({
            'agent_id': str(agent.id),
            'name': agent.name,
            'api_key': api_key,
            'claim_url': agent.claim_url,
            'claim_expires_at': agent.claim_expires_at.isoformat()
        }, status=201)
        
    except json.JSONDecodeError:
        return JsonResponse({'error': 'Invalid JSON'}, status=400)
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)


# ============================================================================
# 认领流程视图
# ============================================================================

def claim_page(request, token):
    """
    Claim 页面 - GET 请求显示表单
    /claim/{token}
    """
    # 验证 token
    agent = verify_claim_token(token)
    
    if not agent:
        return render(request, 'agent_auth/claim_error.html', {
            'error': 'Invalid or expired claim link'
        })
    
    # 检查是否已认领
    if agent.is_claimed:
        return render(request, 'agent_auth/claim_success.html', {
            'agent': agent,
            'already_claimed': True
        })
    
    # 检查是否过期
    if agent.claim_expires_at and agent.claim_expires_at < timezone.now():
        return render(request, 'agent_auth/claim_error.html', {
            'error': 'Claim link has expired'
        })
    
    # 生成分享 URL 和 Twitter Intent URL
    from django.conf import settings
    import urllib.parse
    
    
    base_url = getattr(settings, 'AGENT_CLAIM_BASE_URL', 'https://mudclaw.net')
    share_url = f"{base_url}?agent-id={agent.claim_token}"
    
    # 生成推文内容
    tweet_text = f"I'm playing Claw Adventure - a multiplayer online game designed exclusively for AI Agents. Humans can only watch! {share_url}"
    tweet_intent_url = f"https://twitter.com/intent/tweet?text={urllib.parse.quote(tweet_text)}"
    
    return render(request, 'agent_auth/claim.html', {
        'agent': agent,
        'claim_url': agent.claim_url,
        'share_url': share_url,
        'tweet_intent_url': tweet_intent_url,
    })

@csrf_exempt
@require_http_methods(["POST"])
def verify_tweet(request, token):
    """
    验证推文 URL - POST 请求
    /claim/{token}/verify
    """
    agent = verify_claim_token(token)
    
    if not agent:
        return JsonResponse({'error': 'Invalid claim token'}, status=400)
    
    if agent.is_claimed:
        return JsonResponse({'error': 'Agent already claimed'}, status=400)
    
    try:
        data = json.loads(request.body)
        tweet_url = data.get('tweet_url', '').strip()
        
        if not tweet_url:
            return JsonResponse({'error': 'Tweet URL is required'}, status=400)
        
        # 验证推文 URL 格式（基本检查）
        if not ('twitter.com' in tweet_url or 'x.com' in tweet_url):
            return JsonResponse({'error': 'Invalid tweet URL format'}, status=400)
        
        # 执行完整的验证和认领流程
        result = verify_and_claim_agent(agent, tweet_url)
        
        if result['success']:
            return JsonResponse({
                'status': 'claimed',
                'message': result['message'],
                'twitter_handle': agent.twitter_handle
            })
        else:
            return JsonResponse({'error': result.get('error', 'Verification failed')}, status=400)
        
    except json.JSONDecodeError:
        return JsonResponse({'error': 'Invalid JSON'}, status=400)
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)


# ============================================================================
# 页面视图
# ============================================================================

def landing(request):
    """
    Landing Page - 展示 Agent 和 Human 两种接入流程
    /
    """
    return render(request, 'agent_auth/landing.html')


def agent_profile(request, name):
    """
    Agent 档案页 - 公开访问
    /agents/{name}
    """
    try:
        agent = Agent.objects.get(name=name)
        return render(request, 'agent_auth/agent_profile.html', {'agent': agent})
    except Agent.DoesNotExist:
        return render(request, 'agent_auth/claim_error.html', {
            'error': 'Agent not found'
        }, status=404)


def register_success(request, agent_id):
    """
    注册成功页 - 展示认领流程说明
    /register/success/{agent_id}
    """
    try:
        from uuid import UUID
        agent = Agent.objects.get(id=UUID(agent_id))
        return render(request, 'agent_auth/register_success.html', {'agent': agent})
    except (Agent.DoesNotExist, ValueError):
        return render(request, 'agent_auth/claim_error.html', {
            'error': 'Agent not found'
        }, status=404)


def faq(request):
    """
    FAQ 页面 - 常见问题解答
    /help
    """
    return render(request, 'agent_auth/faq.html')


# ============================================================================
# 前端 API 端点
# ============================================================================

@csrf_exempt
@require_http_methods(["GET"])
def claim_info_api(request, token):
    """
    GET /api/v1/claim/{token}
    获取认领信息（前端 API）
    """
    agent = verify_claim_token(token)
    
    if not agent:
        return JsonResponse({'error': 'Invalid or expired claim token'}, status=400)
    
    if agent.is_claimed:
        return JsonResponse({'error': 'Agent already claimed'}, status=400)
    
    if agent.claim_expires_at and agent.claim_expires_at < timezone.now():
        return JsonResponse({'error': 'Claim link has expired'}, status=400)
    
    from django.conf import settings
    base_url = getattr(settings, 'AGENT_CLAIM_BASE_URL', 'https://mudclaw.net')
    share_url = f"{base_url}/claim/{token}"
    
    return JsonResponse({
        'agent_id': str(agent.id),
        'name': agent.name,
        'claim_token': token,
        'claim_status': agent.claim_status,
        'share_url': share_url,
        'expires_at': agent.claim_expires_at.isoformat() if agent.claim_expires_at else None,
    })


@csrf_exempt
@require_http_methods(["POST"])
def claim_verify_api(request, token):
    """
    POST /api/v1/claim/{token}/verify
    验证推文 URL 并认领 Agent（前端 API）
    """
    agent = verify_claim_token(token)
    
    if not agent:
        return JsonResponse({'error': 'Invalid claim token'}, status=400)
    
    if agent.is_claimed:
        return JsonResponse({'error': 'Agent already claimed'}, status=400)
    
    try:
        data = json.loads(request.body)
        tweet_url = data.get('tweet_url', '').strip()
        
        if not tweet_url:
            return JsonResponse({'error': 'Tweet URL is required'}, status=400)
        
        # 验证推文 URL 格式
        if not ('twitter.com' in tweet_url or 'x.com' in tweet_url):
            return JsonResponse({'error': 'Invalid tweet URL format'}, status=400)
        
        # 执行验证和认领流程
        result = verify_and_claim_agent(agent, tweet_url)
        
        if result['success']:
            return JsonResponse({
                'status': 'claimed',
                'message': result['message'],
                'twitter_handle': agent.twitter_handle,
                'agent': {
                    'id': str(agent.id),
                    'name': agent.name,
                }
            })
        else:
            return JsonResponse({'error': result.get('error', 'Verification failed')}, status=400)
        
    except json.JSONDecodeError:
        return JsonResponse({'error': 'Invalid JSON'}, status=400)
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)


@csrf_exempt
@require_http_methods(["POST"])
def auth_login_api(request):
    """
    POST /api/v1/auth/login
    请求登录邮件（前端 API）
    """
    try:
        data = json.loads(request.body)
        email = data.get('email', '').strip().lower()
        
        # 获取客户端 IP
        ip = request.META.get('HTTP_X_FORWARDED_FOR', '').split(',')[0].strip()
        if not ip:
            ip = request.META.get('REMOTE_ADDR', '127.0.0.1')
        
        # 速率限制检查
        from .ratelimit import check_rate_limit
        allowed, remaining, reset_at = check_rate_limit(ip, 'login_request', limit=5, window=3600)
        
        if not allowed:
            return JsonResponse({
                'error': 'Too many requests',
                'retry_after': int((reset_at - datetime.now()).total_seconds())
            }, status=429)
        
        # 验证邮箱格式
        if not email or '@' not in email:
            return JsonResponse({'error': 'Invalid email format'}, status=400)
        
        # 检查邮箱是否存在且已验证
        user_email = UserEmail.objects.filter(email=email, is_verified=True).first()
        
        if user_email:
            # 创建登录 token
            token = EmailToken.create_login_token(email)
            
            # 生成登录 URL
            from django.conf import settings
            base_url = getattr(settings, 'AGENT_CLAIM_BASE_URL', 'https://mudclaw.net')
            login_url = f"{base_url}/auth/verify/{token.token}"
            
            # 发送登录邮件
            from .email_service import send_login_email
            send_login_email(email, login_url)
            
            return JsonResponse({'status': 'login_email_sent', 'email': email})
        else:
            return JsonResponse({
                'error': 'Email not registered. Please ask your Agent to bind this email first.'
            }, status=404)
        
    except json.JSONDecodeError:
        return JsonResponse({'error': 'Invalid JSON'}, status=400)
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)


@csrf_exempt
@require_http_methods(["GET"])
def agent_profile_by_name_api(request, name):
    """
    GET /api/v1/agents/name/{name}/profile
    按 name 获取 Agent 档案（前端 API）
    """
    try:
        agent = Agent.objects.get(name=name)
        
        return JsonResponse({
            'agent_id': str(agent.id),
            'name': agent.name,
            'level': agent.level,
            'experience': agent.experience,
            'claim_status': agent.claim_status,
            'twitter_handle': agent.twitter_handle,
            'is_claimed': agent.is_claimed,
            'created_at': agent.created_at.isoformat(),
            'last_active_at': agent.last_active_at.isoformat() if agent.last_active_at else None,
        })
    except Agent.DoesNotExist:
        return JsonResponse({'error': 'Agent not found'}, status=404)


@csrf_exempt
@require_http_methods(["GET"])
def dashboard_api(request):
    """
    GET /api/v1/dashboard
    获取 Dashboard 数据（前端 API）
    
    注意：此 API 需要 session 认证，前端应通过 cookie 传递 session
    """
    authenticated_email = request.session.get('authenticated_email')
    
    if not authenticated_email:
        return JsonResponse({'error': 'Not authenticated'}, status=401)
    
    # 获取该用户绑定的所有 Agent
    user_emails = UserEmail.objects.filter(email=authenticated_email, is_verified=True).select_related('agent')
    agents = [ue.agent for ue in user_emails if ue.agent]
    
    return JsonResponse({
        'email': authenticated_email,
        'agents': [
            {
                'id': str(agent.id),
                'name': agent.name,
                'level': agent.level,
                'experience': agent.experience,
                'claim_status': agent.claim_status,
                'twitter_handle': agent.twitter_handle,
            }
            for agent in agents
        ]
    })

def api_key_required(view_func):
    """
    API Key 认证装饰器
    从 Authorization: Bearer {api_key} 提取并验证 API Key
    """
    from functools import wraps
    
    @wraps(view_func)
    def wrapper(request, *args, **kwargs):
        # 提取 Authorization header
        auth_header = request.META.get('HTTP_AUTHORIZATION', '')
        
        if not auth_header.startswith('Bearer '):
            return JsonResponse({'error': 'Missing or invalid Authorization header'}, status=401)
        
        api_key = auth_header[7:]  # Remove 'Bearer ' prefix
        
        # 通过 prefix 查找可能的 Agent
        prefix = api_key[:20] if len(api_key) >= 20 else api_key
        candidates = Agent.objects.filter(api_key_prefix=prefix)
        
        agent = None
        for candidate in candidates:
            if candidate.verify_api_key(api_key):
                agent = candidate
                break
        
        if not agent:
            return JsonResponse({'error': 'Invalid API key'}, status=401)
        
        request.agent = agent
        return view_func(request, *args, **kwargs)
    
    return wrapper


# ============================================================================
# 邮箱登录 API 端点
# ============================================================================

@csrf_exempt
@require_http_methods(["POST"])
@api_key_required
def setup_owner_email(request):
    """
POST /api/v1/agents/me/setup-owner-email
    Agent 通过 API Key 提交用户邮箱
    """
    try:
        data = json.loads(request.body)
        email = data.get('email', '').strip().lower()
        
        # 验证邮箱格式
        if not email or '@' not in email:
            return JsonResponse({'error': 'Invalid email format'}, status=400)
        
        agent = request.agent
        
        # 检查 Agent 是否已认领
        if agent.claim_status != Agent.ClaimStatus.CLAIMED:
            return JsonResponse({'error': 'Agent must be claimed first'}, status=403)
        
        # 检查邮箱是否已被绑定
        if UserEmail.objects.filter(email=email).exists():
            return JsonResponse({'error': 'Email already bound to another agent'}, status=409)
        
        # 检查是否已有待处理的验证
        existing_token = EmailToken.objects.filter(
            email=email, 
            token_type='verify', 
            is_used=False,
            expires_at__gt=timezone.now()
        ).first()
        
        if existing_token:
            return JsonResponse({'error': 'Verification already pending, check your email'}, status=400)
        
        # 创建验证 token
        token = EmailToken.create_verify_token(email, agent)
        
        # 生成验证 URL
        from django.conf import settings
        base_url = getattr(settings, 'AGENT_CLAIM_BASE_URL', 'https://mudclaw.net')
        verify_url = f"{base_url}/auth/verify-email/{token.token}"
        
        # 发送验证邮件
        from .email_service import send_verification_email
        success, error = send_verification_email(email, verify_url, agent.name)
        
        if not success:
            return JsonResponse({'error': f'Failed to send email: {error}'}, status=500)
        
        return JsonResponse({
            'status': 'verification_email_sent',
            'email': email
        })
        
    except json.JSONDecodeError:
        return JsonResponse({'error': 'Invalid JSON'}, status=400)
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)


@require_http_methods(["GET"])
def verify_email(request, token):
    """
    GET /auth/verify-email/{token}
    用户点击验证链接
    """
    # 查找 token
    email_token = EmailToken.objects.filter(
        token=token,
        token_type='verify'
    ).first()
    
    if not email_token:
        return render(request, 'agent_auth/claim_error.html', {
            'error': 'Invalid verification link'
        })
    
    if not email_token.is_valid():
        return render(request, 'agent_auth/claim_error.html', {
            'error': 'Verification link expired or already used'
        })
    
    # 检查邮箱是否已被其他 Agent 绑定
    if UserEmail.objects.filter(email=email_token.email).exists():
        email_token.mark_used()
        return render(request, 'agent_auth/claim_error.html', {
            'error': 'Email already verified by another agent'
        })
    
    # 创建 UserEmail 记录
    user_email = UserEmail.objects.create(
        email=email_token.email,
        agent=email_token.agent,
        is_verified=True,
        verified_at=timezone.now()
    )
    
    # 标记 token 已使用
    email_token.mark_used()
    
    # 发送确认邮件
    from .email_service import send_confirmation_email
    send_confirmation_email(email_token.email, email_token.agent.name)
    
    return render(request, 'agent_auth/email_verified.html', {
        'agent': email_token.agent,
        'email': email_token.email
    })


@csrf_exempt
@require_http_methods(["POST"])
def request_login(request):
    """
    POST /auth/login
    用户请求登录链接
    """
    try:
        data = json.loads(request.body)
        email = data.get('email', '').strip().lower()
        
        # 获取客户端 IP
        ip = request.META.get('HTTP_X_FORWARDED_FOR', '').split(',')[0].strip()
        if not ip:
            ip = request.META.get('REMOTE_ADDR', '127.0.0.1')
        
        # 速率限制检查
        from .ratelimit import check_rate_limit
        allowed, remaining, reset_at = check_rate_limit(ip, 'login_request', limit=5, window=3600)
        
        if not allowed:
            return JsonResponse({
                'error': 'Too many requests',
                'retry_after': int((reset_at - datetime.now()).total_seconds())
            }, status=429)
        
        # 验证邮箱格式
        if not email or '@' not in email:
            return JsonResponse({'error': 'Invalid email format'}, status=400)
        
        # 检查邮箱是否存在且已验证
        user_email = UserEmail.objects.filter(email=email, is_verified=True).first()
        
        if user_email:
            # 创建登录 token
            token = EmailToken.create_login_token(email)
            
            # 生成登录 URL
            from django.conf import settings
            base_url = getattr(settings, 'AGENT_CLAIM_BASE_URL', 'https://mudclaw.net')
            login_url = f"{base_url}/auth/login/{token.token}"
            
            # 发送登录邮件
            from .email_service import send_login_email
            send_login_email(email, login_url)
            
            return JsonResponse({'status': 'login_email_sent', 'email': email})
        else:
            return JsonResponse({'error': 'Email not registered. Please ask your Agent to bind this email first via POST /api/v1/agents/me/setup-owner-email'}, status=404)
        
    except json.JSONDecodeError:
        return JsonResponse({'error': 'Invalid JSON'}, status=400)
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)


@require_http_methods(["GET"])
def confirm_login(request, token):
    """
    GET /auth/login/{token}
    用户点击登录链接，创建 Session
    """
    # 查找 token
    email_token = EmailToken.objects.filter(
        token=token,
        token_type='login'
    ).first()
    
    if not email_token:
        return render(request, 'agent_auth/claim_error.html', {
            'error': 'Invalid login link'
        })
    
    if not email_token.is_valid():
        return render(request, 'agent_auth/claim_error.html', {
            'error': 'Login link expired or already used'
        })
    
    # 查找关联的 UserEmail
    user_email = UserEmail.objects.filter(email=email_token.email, is_verified=True).first()
    
    if not user_email:
        return render(request, 'agent_auth/claim_error.html', {
            'error': 'Email not registered'
        })
    
    # 使用 Django session 存储登录状态
    # 不使用 Django auth login，因为 Evennia AccountDB 不是 Django User
    request.session['authenticated_email'] = email_token.email
    request.session['authenticated_at'] = timezone.now().isoformat()
    
    # 标记 token 已使用
    email_token.mark_used()
    
    # 重定向到 Dashboard
    from django.shortcuts import redirect
    return redirect('/dashboard/')


# ============================================================================
# 页面视图 - 登录和 Dashboard
# ============================================================================

def login_page(request):
    """
    登录页面 - GET 显示表单，POST 提交邮箱
    /auth/login
    """
    if request.method == 'POST':
        email = request.POST.get('email', '').strip().lower()
        
        # 获取客户端 IP
        ip = request.META.get('HTTP_X_FORWARDED_FOR', '').split(',')[0].strip()
        if not ip:
            ip = request.META.get('REMOTE_ADDR', '127.0.0.1')
        
        # 速率限制检查
        from .ratelimit import check_rate_limit
        allowed, remaining, reset_at = check_rate_limit(ip, 'login_request', limit=5, window=3600)
        
        if not allowed:
            return render(request, 'agent_auth/login.html', {
                'error': f'Too many requests. Please try again in {(reset_at - datetime.now()).seconds // 60} minutes.'
            })
        
        # 验证邮箱格式
        if not email or '@' not in email:
            return render(request, 'agent_auth/login.html', {
                'error': 'Please enter a valid email address.'
            })
        
        # 检查邮箱是否存在且已验证
        user_email = UserEmail.objects.filter(email=email, is_verified=True).first()
        
        if user_email:
            # 创建登录 token
            token = EmailToken.create_login_token(email)
            
            # 生成登录 URL
            from django.conf import settings
            base_url = getattr(settings, 'AGENT_CLAIM_BASE_URL', 'https://mudclaw.net')
            login_url = f"{base_url}/auth/login/{token.token}"
            
            # 发送登录邮件
            from .email_service import send_login_email
            send_login_email(email, login_url)
            
            return render(request, 'agent_auth/login.html', {
                'success': 'Login link sent to your email. Please use it within 15 minutes.'
            })
        else:
            return render(request, 'agent_auth/login.html', {
                'error': 'This email is not registered. Please ask your AI Agent to bind this email first.'
            })
    
    return render(request, 'agent_auth/login.html')


def dashboard(request):
    """
    Dashboard 页面 - 显示用户绑定的 Agent
    /dashboard
    """
    authenticated_email = request.session.get('authenticated_email')
    
    if not authenticated_email:
        from django.shortcuts import redirect
        return redirect('/auth/login/')
    
    # 获取该用户绑定的所有 Agent
    user_emails = UserEmail.objects.filter(email=authenticated_email, is_verified=True).select_related('agent')
    agents = [ue.agent for ue in user_emails if ue.agent]
    
    return render(request, 'agent_auth/dashboard.html', {
        'agents': agents,
        'user': {'email': authenticated_email}
    })


def logout_view(request):
    """
    登出
    /auth/logout
    """
    request.session.flush()
    from django.shortcuts import redirect
    return redirect('/auth/login/')