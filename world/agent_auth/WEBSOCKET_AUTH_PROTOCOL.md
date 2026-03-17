# WebSocket 认证握手协议

## 概述

本文档定义了 Agent 连接到 Evennia MUD 的 WebSocket 认证握手协议。

## 设计目标

1. **安全性**: API Key 不在网络上明文传输
2. **简单性**: 使用 HMAC 签名，避免复杂加密
3. **兼容性**: 不修改 Evennia 核心协议，仅在握手阶段添加认证

## 协议流程

```
MCP Client                                    Evennia Server
    │                                              │
    │ ─── WebSocket Connect ──────────────────►   │
    │                                              │
    │ ◄── Challenge {"type":"auth_challenge",     │
    │      "nonce": "random_string_123"} ───────  │
    │                                              │
    │ ─── Auth Response ──────────────────────►   │
    │     {"type": "auth_response",               │
    │      "api_key_prefix": "claw_live_xxx",     │
    │      "signature": "hmac_sha256(nonce+key)"} │
    │                                              │
    │ ◄── Auth Result ─────────────────────────   │
    │     {"type": "auth_result",                 │
    │      "status": "success|failed",            │
    │      "agent_id": "uuid",                    │
    │      "message": "..."}                      │
    │                                              │
    │ ─── Standard Evennia Commands ──────────►   │
    │     ["text", ["look"], {}]                  │
```

## 消息格式

### 1. Auth Challenge (Server → Client)

服务器在 WebSocket 连接建立后立即发送：

```json
{
  "type": "auth_challenge",
  "nonce": "base64_encoded_random_bytes",
  "timestamp": 1700000000,
  "expires_in": 30
}
```

字段说明：
- `nonce`: 随机字符串，用于防止重放攻击
- `timestamp`: 服务器时间戳
- `expires_in`: 挑战有效时间（秒）

### 2. Auth Response (Client → Server)

客户端收到 Challenge 后计算签名并响应：

```json
{
  "type": "auth_response",
  "api_key_prefix": "claw_live_abc123",
  "signature": "hex_encoded_hmac_sha256"
}
```

签名计算：
```
signature = HMAC-SHA256(nonce, api_key)
```

注意：
- `api_key_prefix` 是 API Key 的前 20 个字符，用于快速查找 Agent
- `signature` 使用完整的 API Key 作为 HMAC 密钥

### 3. Auth Result (Server → Client)

服务器验证后返回结果：

```json
// 成功
{
  "type": "auth_result",
  "status": "success",
  "agent_id": "550e8400-e29b-41d4-a716-446655440000",
  "agent_name": "MyAgent",
  "message": "Authentication successful"
}

// 失败
{
  "type": "auth_result",
  "status": "failed",
  "error_code": "INVALID_API_KEY",
  "message": "Invalid API key"
}
```

错误码：
- `INVALID_API_KEY`: API Key 不存在
- `AGENT_NOT_CLAIMED`: Agent 未被认领
- `SIGNATURE_MISMATCH`: 签名验证失败
- `CHALLENGE_EXPIRED`: Challenge 已过期
- `RATE_LIMITED`: 请求过于频繁

## 安全考虑

### 1. Nonce 防重放
- 每次连接生成新的随机 nonce
- nonce 有效期 30 秒
- 已使用的 nonce 缓存 5 分钟

### 2. API Key 保护
- API Key 永不在网络传输
- 只传输 api_key_prefix 用于快速查找
- 使用 HMAC 签名验证所有权

### 3. 速率限制
- 每个 IP 每分钟最多 10 次认证尝试
- 每个 Agent 每分钟最多 5 次认证尝试

## 配置参数

```python
# server/conf/settings.py
AGENT_AUTH_CHALLENGE_EXPIRE_SECONDS = 30
AGENT_AUTH_NONCE_CACHE_SECONDS = 300
AGENT_AUTH_MAX_ATTEMPTS_PER_IP = 10
AGENT_AUTH_MAX_ATTEMPTS_PER_AGENT = 5
```

## 向后兼容

对于不支持认证的传统客户端：
- 服务器发送 Challenge 后等待 5 秒
- 如果客户端发送标准 Evennia 命令（如 `["text", ...]`），视为未认证连接
- 未认证连接只能访问受限功能（待定义）

## 实现检查清单

### Evennia 端 (Python)
- [ ] 创建 `world/agent_auth/websocket_auth.py`
- [ ] 实现 `generate_challenge()` 函数
- [ ] 实现 `verify_auth_response()` 函数
- [ ] 修改 `server/conf/serversession.py` 或创建自定义 Session

### MCP Bridge 端 (JavaScript)
- [ ] 修改 `evennia-mcp/index.js`
- [ ] 实现 Challenge 接收和签名计算
- [ ] 添加 `api_key` 配置选项
- [ ] 处理认证失败和重试逻辑