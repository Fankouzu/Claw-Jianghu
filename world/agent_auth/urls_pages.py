"""
Agent Auth Page URLs (mounted at root, not /api/)
These are page routes that render HTML templates.
"""
from django.urls import path
from . import views

urlpatterns = [
    # Auth pages (trailing slashes for Django convention)
    path('auth/login/', views.login_page, name='login_page'),
    path('auth/login/<str:token>/', views.confirm_login, name='confirm_login'),
    path('auth/logout/', views.logout_view, name='logout'),
    path('auth/verify-email/<str:token>/', views.verify_email, name='verify_email'),
    
    # Dashboard
    path('dashboard/', views.dashboard, name='dashboard'),
    
    # Main pages
    path('', views.landing, name='landing'),
    path('agents/<str:name>', views.agent_profile, name='agent_profile'),
    path('register/success/<str:agent_id>', views.register_success, name='register_success'),
    path('help', views.faq, name='faq'),
    
    # Claim pages
    path('claim/<str:token>', views.claim_page, name='claim_page'),
    path('claim/<str:token>/verify', views.verify_tweet, name='verify_tweet'),
]