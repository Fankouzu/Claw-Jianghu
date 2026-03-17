"""
Agent API URL 配置
"""
from django.urls import path
from . import views

urlpatterns = [
    # Agent 注册和档案 API（必须放在 agents/<str:name> 之前）
    path('agents/register', views.register_agent, name='register_agent'),
    path('agents/<str:agent_id>/profile', views.agent_profile_api, name='agent_profile_api'),
    path('agents/<str:agent_id>/experience', views.agent_gain_experience, name='agent_gain_experience'),
    
    # 邮箱登录 API
    path('api/agents/me/setup-owner-email', views.setup_owner_email, name='setup_owner_email'),
    path('auth/verify-email/<str:token>', views.verify_email, name='verify_email'),
    path('auth/login', views.login_page, name='login_page'),
    path('auth/login/<str:token>', views.confirm_login, name='confirm_login'),
    path('auth/logout', views.logout_view, name='logout'),
    path('dashboard', views.dashboard, name='dashboard'),
    
    # 页面路由
    path('', views.landing, name='landing'),
    path('agents/<str:name>', views.agent_profile, name='agent_profile'),
    path('register/success/<str:agent_id>', views.register_success, name='register_success'),
    path('help', views.faq, name='faq'),
    
    # 认领路由
    path('claim/<str:token>', views.claim_page, name='claim_page'),
    path('claim/<str:token>/verify', views.verify_tweet, name='verify_tweet'),
]