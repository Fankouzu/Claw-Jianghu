from django.apps import AppConfig


class AgentAuthConfig(AppConfig):
    """
    Agent 认领系统 Django App 配置
    """
    name = 'world.agent_auth'
    verbose_name = 'Agent Authentication'
    
    def ready(self):
        """
        App 启动时的初始化
        """
        pass