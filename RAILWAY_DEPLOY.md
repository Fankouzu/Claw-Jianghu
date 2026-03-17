# Railway Deployment Guide

## 架构概述

```
┌─────────────────────────────────────────────────────────────┐
│                         Railway                              │
│                                                              │
│  ┌─────────────────┐  ┌─────────────────────────────────┐  │
│  │   PostgreSQL    │  │       Game Backend               │  │
│  │   (数据库)       │  │  ┌─────────────────────────┐    │  │
│  └────────┬────────┘  │  │ Nginx (:$PORT)          │    │  │
│           │           │  │   ├─ /      → HTTP:4001 │    │  │
│           │           │  │   └─ /ws    → WS:4002   │    │  │
│           │           │  └─────────────────────────┘    │  │
│           │           │  ┌─────────────────────────┐    │  │
│           │           │  │ Evennia Portal+Server   │    │  │
│           │           │  │   HTTP:4001, WS:4002    │    │  │
│           │           │  └─────────────────────────┘    │  │
│           │           └─────────────────────────────────┘  │
│           │                                                   │
│           │           ┌─────────────────────────────────┐  │
│           └──────────►│       Web Frontend               │  │
│                       │  Django + Gunicorn (:$PORT)      │  │
│                       └─────────────────────────────────┘  │
│                                                              │
└─────────────────────────────────────────────────────────────┘
```

## 部署步骤

### 1. 创建 Railway 项目

```bash
railway login
railway init
```

### 2. 添加 PostgreSQL 服务

```bash
railway add --plugin postgresql
```

### 3. 部署 Game Backend

创建服务并配置：

```bash
# 设置环境变量
railway variables set DJANGO_SETTINGS_MODULE=server.conf.railway_settings
railway variables set SECRET_KEY=your-secret-key-here
railway variables set WEBSOCKET_CLIENT_URL=wss://your-game-domain.com/ws
railway variables set ALLOWED_HOSTS=your-game-domain.com
railway variables set DEBUG=False

# 部署
railway up --service game-backend
```

### 4. 初始化数据库

```bash
# 运行迁移
railway run --service game-backend -- evennia migrate

# 创建超级用户
railway run --service game-backend -- evennia createsuperuser
```

### 5. 部署 Web Frontend

```bash
# 设置环境变量
railway variables set DJANGO_SETTINGS_MODULE=web_frontend.settings_railway
railway variables set SECRET_KEY=your-secret-key-here
railway variables set GAME_WEBSOCKET_URL=wss://your-game-domain.com/ws
railway variables set ALLOWED_HOSTS=your-www-domain.com
railway variables set DEBUG=False

# 部署
railway up --service web-frontend
```

### 6. 配置域名

在 Railway 控制面板中配置自定义域名：

- **Game Backend**: `game.your-domain.com`
- **Web Frontend**: `www.your-domain.com`

## 环境变量清单

### Game Backend (`Dockerfile.backend`)

| 变量名 | 必需 | 说明 |
|--------|------|------|
| `DATABASE_URL` | ✅ | PostgreSQL 连接字符串（Railway 自动提供） |
| `SECRET_KEY` | ✅ | Django 密钥 |
| `WEBSOCKET_CLIENT_URL` | ✅ | WebSocket URL，格式：`wss://game.your-domain.com/ws` |
| `ALLOWED_HOSTS` | ✅ | 允许的主机名 |
| `DEBUG` | | 调试模式，默认 `False` |

### Web Frontend (`Dockerfile.frontend`)

| 变量名 | 必需 | 说明 |
|--------|------|------|
| `DATABASE_URL` | ✅ | PostgreSQL 连接字符串（引用 PostgreSQL 服务） |
| `SECRET_KEY` | ✅ | Django 密钥（与 Backend 相同） |
| `GAME_WEBSOCKET_URL` | ✅ | 游戏后端 WebSocket 地址 |
| `ALLOWED_HOSTS` | ✅ | 允许的主机名 |
| `DEBUG` | | 调试模式，默认 `False` |

## 故障排查

### 查看日志

```bash
railway logs --service game-backend
railway logs --service web-frontend
```

### 常见问题

1. **WebSocket 连接失败**
   - 检查 `WEBSOCKET_CLIENT_URL` 是否正确设置
   - 确保域名已正确配置 SSL

2. **数据库连接失败**
   - 检查 `DATABASE_URL` 环境变量
   - 确认 PostgreSQL 服务正在运行

3. **静态文件 404**
   - 前端启动时会自动运行 `collectstatic`
   - 检查 `STATIC_ROOT` 目录权限