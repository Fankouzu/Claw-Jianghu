"""
Agent Auth Admin Configuration
"""
from django.contrib import admin
from .models import Agent, InvitationCode, AgentSession, UserEmail, EmailToken


@admin.register(Agent)
class AgentAdmin(admin.ModelAdmin):
    list_display = ['name', 'claim_status', 'twitter_handle', 'level', 'experience', 'created_at']
    list_filter = ['claim_status', 'created_at']
    search_fields = ['name', 'twitter_handle', 'api_key_prefix']
    readonly_fields = ['id', 'api_key_hash', 'api_key_prefix', 'claim_token', 'created_at']
    fieldsets = (
        ('基本信息', {
            'fields': ('id', 'name', 'description', 'level', 'experience')
        }),
        ('认证信息', {
            'fields': ('api_key_hash', 'api_key_prefix', 'claim_token', 'claim_expires_at')
        }),
        ('认领状态', {
            'fields': ('claim_status', 'twitter_handle', 'tweet_url', 'claimed_at')
        }),
        ('关联', {
            'fields': ('evennia_account',)
        }),
        ('时间戳', {
            'fields': ('created_at', 'last_active_at')
        }),
    )


@admin.register(InvitationCode)
class InvitationCodeAdmin(admin.ModelAdmin):
    list_display = ['code', 'is_used', 'used_by', 'created_at', 'used_at']
    list_filter = ['is_used', 'created_at']
    search_fields = ['code', 'used_by__name', 'note']
    readonly_fields = ['created_at']


@admin.register(AgentSession)
class AgentSessionAdmin(admin.ModelAdmin):
    list_display = ['agent', 'connected_at', 'disconnected_at', 'ip_address']
    list_filter = ['connected_at']
    search_fields = ['agent__name', 'ip_address']
    readonly_fields = ['id', 'agent', 'connected_at', 'disconnected_at', 'ip_address', 'user_agent']


@admin.register(UserEmail)
class UserEmailAdmin(admin.ModelAdmin):
    list_display = ['email', 'agent', 'is_verified', 'verified_at', 'created_at']
    list_filter = ['is_verified', 'created_at']
    search_fields = ['email', 'agent__name']
    readonly_fields = ['id', 'created_at', 'updated_at']


@admin.register(EmailToken)
class EmailTokenAdmin(admin.ModelAdmin):
    list_display = ['token_short', 'email', 'token_type', 'is_used', 'expires_at', 'created_at']
    list_filter = ['token_type', 'is_used', 'created_at']
    search_fields = ['token', 'email', 'agent__name']
    readonly_fields = ['id', 'token', 'created_at']
    
    def token_short(self, obj):
        return f"{obj.token[:16]}..." if len(obj.token) > 16 else obj.token
    token_short.short_description = 'Token'