"""
Agent 认领系统测试

测试 Agent 注册、认领、认证等核心流程。
"""
from evennia.utils.test_resources import EvenniaTest
from django.test import TestCase
from django.test.client import Client
import json
from uuid import UUID

from world.agent_auth.models import Agent, AgentSession
from world.agent_auth.auth import verify_api_key, verify_claim_token, check_claim_status
from world.agent_auth.twitter_verify import extract_tweet_id, extract_twitter_handle


class AgentModelTest(TestCase):
    """测试 Agent 模型"""
    
    def test_create_agent(self):
        """测试创建 Agent"""
        agent, api_key = Agent.create_agent(
            name="TestAgent",
            description="A test agent"
        )
        
        self.assertIsNotNone(agent)
        self.assertEqual(agent.name, "TestAgent")
        self.assertEqual(agent.claim_status, Agent.ClaimStatus.PENDING)
        self.assertTrue(api_key.startswith("claw_live_"))
        
    def test_api_key_hashing(self):
        """测试 API Key 哈希"""
        agent, api_key = Agent.create_agent(name="HashTest")
        
        # 验证 hash 不等于明文
        self.assertNotEqual(agent.api_key_hash, api_key)
        
        # 验证 API Key 验证函数
        self.assertTrue(agent.verify_api_key(api_key))
        self.assertFalse(agent.verify_api_key("invalid_key"))
        
    def test_claim_url_generation(self):
        """测试 Claim URL 生成"""
        agent, _ = Agent.create_agent(name="URLTest")
        
        self.assertIsNotNone(agent.claim_url)
        self.assertTrue("/claim/" in agent.claim_url)
        self.assertTrue(agent.claim_token in agent.claim_url)


class AgentAuthTest(TestCase):
    """测试 Agent 认证函数"""
    
    def setUp(self):
        self.agent, self.api_key = Agent.create_agent(name="AuthTest")
    
    def test_verify_api_key_valid(self):
        """测试有效的 API Key 验证"""
        result = verify_api_key(self.api_key)
        self.assertIsNotNone(result)
        self.assertEqual(result.id, self.agent.id)
        
    def test_verify_api_key_invalid(self):
        """测试无效的 API Key 验证"""
        result = verify_api_key("claw_live_invalid_key")
        self.assertIsNone(result)
        
    def test_verify_claim_token_valid(self):
        """测试有效的 Claim Token 验证"""
        result = verify_claim_token(self.agent.claim_token)
        self.assertIsNotNone(result)
        self.assertEqual(result.id, self.agent.id)
        
    def test_verify_claim_token_invalid(self):
        """测试无效的 Claim Token 验证"""
        result = verify_claim_token("invalid_token")
        self.assertIsNone(result)


class TwitterVerifyTest(TestCase):
    """测试推文验证函数"""
    
    def test_extract_tweet_id_twitter_com(self):
        """测试从 twitter.com URL 提取 tweet_id"""
        url = "https://twitter.com/testuser/status/1234567890123456789"
        tweet_id = extract_tweet_id(url)
        self.assertEqual(tweet_id, "1234567890123456789")
        
    def test_extract_tweet_id_x_com(self):
        """测试从 x.com URL 提取 tweet_id"""
        url = "https://x.com/testuser/status/9876543210987654321"
        tweet_id = extract_tweet_id(url)
        self.assertEqual(tweet_id, "9876543210987654321")
        
    def test_extract_tweet_id_invalid(self):
        """测试无效 URL"""
        url = "https://example.com/not-a-tweet"
        tweet_id = extract_tweet_id(url)
        self.assertIsNone(tweet_id)
        
    def test_extract_twitter_handle(self):
        """测试提取 Twitter 用户名"""
        url = "https://x.com/myusername/status/123456789"
        handle = extract_twitter_handle(url)
        self.assertEqual(handle, "myusername")


class AgentAPITest(TestCase):
    """测试 Agent API 端点"""
    
    def setUp(self):
        self.client = Client()
        # 创建测试邀请码
        from world.agent_auth.models import InvitationCode
        self.inv_code = InvitationCode.objects.create(code='INV-TEST12345678')
    
    def test_register_agent_success(self):
        """测试成功注册 Agent"""
        response = self.client.post(
            '/api/agents/register',
            data=json.dumps({
                'name': 'APIAgent', 
                'description': 'Test',
                'invitation_code': 'INV-TEST12345678'
            }),
            content_type='application/json'
        )
        
        self.assertEqual(response.status_code, 201)
        data = response.json()
        
        self.assertIn('agent_id', data)
        self.assertEqual(data['name'], 'APIAgent')
        self.assertIn('api_key', data)
        self.assertTrue(data['api_key'].startswith('claw_'))
        self.assertIn('claim_url', data)
    
    def test_register_agent_missing_name(self):
        """测试缺少名称"""
        response = self.client.post(
            '/api/agents/register',
            data=json.dumps({
                'description': 'No name',
                'invitation_code': 'INV-TEST12345678'
            }),
            content_type='application/json'
        )
        
        self.assertEqual(response.status_code, 400)
        data = response.json()
        self.assertEqual(data['error'], 'name is required')
    
    def test_register_agent_missing_invitation_code(self):
        """测试缺少邀请码"""
        response = self.client.post(
            '/api/agents/register',
            data=json.dumps({'name': 'NoCode', 'description': 'Test'}),
            content_type='application/json'
        )
        
        self.assertEqual(response.status_code, 400)
        data = response.json()
        self.assertEqual(data['error'], 'invitation_code is required')
    
    def test_register_agent_invalid_invitation_code(self):
        """测试无效邀请码"""
        response = self.client.post(
            '/api/agents/register',
            data=json.dumps({
                'name': 'InvalidCode',
                'description': 'Test',
                'invitation_code': 'INV-INVALID12345'
            }),
            content_type='application/json'
        )
        
        self.assertEqual(response.status_code, 400)
        data = response.json()
        self.assertEqual(data['error'], 'Invalid invitation code')
    
    def test_register_agent_used_invitation_code(self):
        """测试已使用的邀请码"""
        # 先用邀请码注册一次
        self.client.post(
            '/api/agents/register',
            data=json.dumps({
                'name': 'FirstAgent',
                'description': 'Test',
                'invitation_code': 'INV-TEST12345678'
            }),
            content_type='application/json'
        )
        
        # 再用相同邀请码注册
        response = self.client.post(
            '/api/agents/register',
            data=json.dumps({
                'name': 'SecondAgent',
                'description': 'Test',
                'invitation_code': 'INV-TEST12345678'
            }),
            content_type='application/json'
        )
        
        self.assertEqual(response.status_code, 400)
        data = response.json()
        self.assertEqual(data['error'], 'Invitation code already used')
    
    def test_register_agent_duplicate_name(self):
        """测试重复名称注册"""
        # 创建另一个邀请码
        from world.agent_auth.models import InvitationCode
        inv_code2 = InvitationCode.objects.create(code='INV-TEST99999999')
        
        # 第一次注册
        self.client.post(
            '/api/agents/register',
            data=json.dumps({
                'name': 'DuplicateAgent',
                'description': 'Test',
                'invitation_code': 'INV-TEST12345678'
            }),
            content_type='application/json'
        )
        
        # 第二次注册相同名称（用新邀请码）
        response = self.client.post(
            '/api/agents/register',
            data=json.dumps({
                'name': 'DuplicateAgent',
                'description': 'Test',
                'invitation_code': 'INV-TEST99999999'
            }),
            content_type='application/json'
        )
        
        self.assertEqual(response.status_code, 409)
        data = response.json()
        self.assertEqual(data['error'], 'Agent name already exists')
    
    def test_register_agent_invalid_json(self):
        """测试无效 JSON"""
        response = self.client.post(
            '/api/agents/register',
            data='not valid json',
            content_type='application/json'
        )
        
        self.assertEqual(response.status_code, 400)
        data = response.json()
        self.assertEqual(data['error'], 'Invalid JSON')

class ClaimPageTest(TestCase):
    """测试 Claim 页面"""
    
    def setUp(self):
        self.client = Client()
        self.agent, self.api_key = Agent.create_agent(name="ClaimPageTest")
    
    def test_claim_page_valid_token(self):
        """测试有效的 Claim Token 访问页面"""
        response = self.client.get(f'/claim/{self.agent.claim_token}')
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, self.agent.name)
        
    def test_claim_page_invalid_token(self):
        """测试无效的 Claim Token"""
        response = self.client.get('/claim/invalid_token_12345')
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Invalid')


class AgentSessionTest(TestCase):
    """测试 Agent 会话"""
    
    def setUp(self):
        self.agent, _ = Agent.create_agent(name="SessionTest")
    
    def test_create_session(self):
        """测试创建会话记录"""
        session = AgentSession.objects.create(
            agent=self.agent,
            ip_address="127.0.0.1",
            user_agent="Test Client"
        )
        
        self.assertIsNotNone(session.id)
        self.assertEqual(session.agent, self.agent)
        self.assertIsNone(session.disconnected_at)
        
    def test_session_duration(self):
        """测试会话持续时间计算"""
        from django.utils import timezone
        from datetime import timedelta
        
        session = AgentSession.objects.create(
            agent=self.agent,
            ip_address="127.0.0.1"
        )
        
        # 未断开，应该返回 None
        self.assertIsNone(session.duration_seconds)
        
        # 断开后
        session.disconnected_at = session.connected_at + timedelta(minutes=5)
        session.save()
        
        # 应该约 300 秒
        self.assertAlmostEqual(session.duration_seconds, 300, delta=1)