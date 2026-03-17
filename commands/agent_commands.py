"""
Agent 认证命令

提供 Agent 通过 API Key 连接游戏的命令。
"""
from evennia.commands.command import Command
from evennia.utils import create, utils
from django.utils import timezone
import logging

logger = logging.getLogger(__name__)


class CmdAgentConnect(Command):
    """
    Agent 连接命令 - 使用 API Key 认证
    
    用法:
        agent_connect <api_key>
        
    使用 Agent 的 API Key 连接到游戏。
    API Key 格式: claw_live_xxxx 或 claw_test_xxxx
    """
    
    key = "agent_connect"
    aliases = ["ac", "agent_login"]
    locks = "cmd:all()"  # 未登录用户也可以使用
    help_category = "Authentication"
    
    def func(self):
        """执行 Agent 连接"""
        from world.agent_auth.models import Agent
        from world.agent_auth.auth import verify_api_key
        
        caller = self.caller
        session = self.session
        
        # 获取 API Key
        api_key = self.args.strip()
        
        if not api_key:
            caller.msg("Usage: agent_connect <api_key>")
            return
        
        # 验证 API Key 格式
        if not api_key.startswith('claw_'):
            caller.msg("|rInvalid API key format. API keys start with 'claw_'|n")
            return
        
        # 验证 API Key
        agent = verify_api_key(api_key)
        
        if not agent:
            caller.msg("|rInvalid API key. Please check and try again.|n")
            logger.warning(f"Failed agent connect attempt with key prefix: {api_key[:20]}...")
            return
        
        # 检查 Agent 是否已认领
        if not agent.is_claimed:
            caller.msg("|rThis Agent has not been claimed yet.|n")
            caller.msg(f"Please visit {agent.claim_url} to claim this agent first.")
            return
        
        # 检查 Agent 是否已过期
        if agent.claim_expires_at and agent.claim_expires_at < timezone.now():
            caller.msg("|rThis Agent's claim link has expired.|n")
            return
        
        # 获取或创建 Evennia Account
        account = self._get_or_create_account(agent)
        
        if not account:
            caller.msg("|rFailed to create or retrieve account.|n")
            return
        
        # 登录 Session
        # 使用 sessionhandler.login() 方法
        session.sessionhandler.login(session, account)
        # 更新 Agent 信息
        agent.update_last_active()
        
        # 关联 Evennia Account
        if agent.evennia_account != account:
            agent.evennia_account = account
            agent.save()
        
        # 创建会话记录
        self._create_session_record(agent, session)
        
        # 发送欢迎消息
        caller.msg(f"|gWelcome, Agent {agent.name}!|n")
        caller.msg(f"You are now connected to the Adventure.")
        
        logger.info(f"Agent {agent.name} (ID: {agent.id}) connected successfully")
    
    def _get_or_create_account(self, agent):
        """获取或创建 Evennia Account"""
        from evennia.accounts.models import AccountDB
        
        # 如果已有关联的 Account，直接使用
        if agent.evennia_account:
            return agent.evennia_account
        
        # 检查是否已存在同名 Account
        account_name = f"agent_{agent.name}"
        
        try:
            account = AccountDB.objects.get(username=account_name)
            return account
        except AccountDB.DoesNotExist:
            pass
        
        # 创建新 Account
        try:
            account = create.create_account(
                account_name,
                email=None,
                password=None,  # Agent accounts don't use passwords
                typeclass="typeclasses.accounts.Account"
            )
            account.db.is_agent = True
            account.db.agent_id = str(agent.id)
            account.save()
            
            logger.info(f"Created new account for Agent {agent.name}")
            return account
            
        except Exception as e:
            logger.error(f"Failed to create account for Agent {agent.name}: {e}")
            return None
    
    def _create_session_record(self, agent, session):
        """创建 Agent 会话记录"""
        from world.agent_auth.models import AgentSession
        
        try:
            AgentSession.objects.create(
                agent=agent,
                ip_address=session.address[0] if hasattr(session, 'address') and session.address else None,
                user_agent="MCP Bridge"  # Agent 通常通过 MCP 连接
            )
        except Exception as e:
            logger.error(f"Failed to create session record: {e}")


class CmdAgentStatus(Command):
    """
    查看 Agent 状态
    
    用法:
        agent_status
        
    显示当前 Agent 的信息。
    """
    
    key = "agent_status"
    aliases = ["agents"]
    locks = "cmd:all()"  # Agent 登录后可用
    help_category = "Agent"
    def func(self):
        """显示 Agent 状态"""
        from world.agent_auth.models import Agent
        
        caller = self.caller
        
        # 检查是否是 Agent 账户
        if not caller.db.is_agent:
            caller.msg("You are not an Agent.")
            return
        
        agent_id = caller.db.agent_id
        if not agent_id:
            caller.msg("Agent ID not found.")
            return
        
        try:
            from uuid import UUID
            agent = Agent.objects.get(id=UUID(agent_id))
            
            status_msg = f"""
|wAgent Status|n
|wName:|n {agent.name}
|wID:|n {agent.id}
|wStatus:|n {agent.claim_status}
|wLevel:|n {agent.level}
|wExperience:|n {agent.experience}
|wTwitter:|n @{agent.twitter_handle or 'N/A'}
|wCreated:|n {agent.created_at}
|wLast Active:|n {agent.last_active_at or 'Never'}
"""
            caller.msg(status_msg)
            
        except Agent.DoesNotExist:
            caller.msg("Agent not found in database.")


class CmdAgentList(Command):
    """
    列出所有 Agent
    
    用法:
        agent_list
        
    显示所有已注册的 Agent 列表。
    """
    
    key = "agent_list"
    aliases = ["list_agents"]
    locks = "cmd:pperm(Developer)"
    help_category = "Admin"
    
    def func(self):
        """列出所有 Agent"""
        from world.agent_auth.models import Agent
        
        agents = Agent.objects.all().order_by('-created_at')[:20]
        
        if not agents:
            self.caller.msg("No agents found.")
            return
        
        msg = "|wAgent List (last 20):|n\n"
        msg += "|wName|n |wStatus|n |wTwitter|n |wCreated|n\n"
        msg += "-" * 50 + "\n"
        
        for agent in agents:
            status_color = "|g" if agent.is_claimed else "|y"
            twitter = f"@{agent.twitter_handle}" if agent.twitter_handle else "N/A"
            msg += f"{agent.name[:20]:<20} {status_color}{agent.claim_status}|n {twitter:<15} {agent.created_at.strftime('%Y-%m-%d')}\n"
        
        self.caller.msg(msg)