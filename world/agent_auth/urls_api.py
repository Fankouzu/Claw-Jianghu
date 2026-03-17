"""
Agent API URL 配置（挂载到 /api/v1/）
"""
from django.urls import path
from . import views

urlpatterns = [
    # Agent 注册和档案 API
    path('agents/register', views.register_agent, name='register_agent'),
    path('agents/<str:agent_id>/profile', views.agent_profile_api, name='agent_profile_api'),
    path('agents/<str:agent_id>/experience', views.agent_gain_experience, name='agent_gain_experience'),
    path('agents/name/<str:name>/profile', views.agent_profile_by_name_api, name='agent_profile_by_name_api'),
    
    # 邮箱绑定 API (需要 API Key 认证)
    path('agents/me/setup-owner-email', views.setup_owner_email, name='setup_owner_email'),
    
    # Claim API (前端)
    path('claim/<str:token>', views.claim_info_api, name='claim_info_api'),
    path('claim/<str:token>/verify', views.claim_verify_api, name='claim_verify_api'),
    
    # Auth API (前端)
    path('auth/login', views.auth_login_api, name='auth_login_api'),
    
    # Dashboard API (前端)
    path('dashboard', views.dashboard_api, name='dashboard_api'),
]