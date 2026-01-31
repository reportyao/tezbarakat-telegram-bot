# Tezbarakat Telegram Bot - 生产环境部署指南

## 1. 服务器要求

### 硬件配置
| 配置项 | 最低要求 | 推荐配置 |
|-------|---------|---------|
| CPU | 2 核 | 4 核 |
| 内存 | 4 GB | 8 GB |
| 硬盘 | 40 GB SSD | 80 GB SSD |
| 带宽 | 3 Mbps | 5 Mbps |

### 操作系统
- **推荐**: Ubuntu 22.04 LTS
- **支持**: CentOS 7.9+, Debian 11+

### 网络要求
- 服务器需要能够访问 Telegram API（建议使用香港、新加坡等海外地域）
- 如使用国内服务器，需要配置代理

## 2. 安全配置清单

### 2.1 必须修改的配置

在部署前，**必须**修改以下配置：

```bash
# 复制环境变量模板
cp .env.example .env

# 编辑 .env 文件
nano .env
```

**必须修改的配置项：**

| 配置项 | 说明 | 示例 |
|-------|------|------|
| `POSTGRES_PASSWORD` | 数据库密码 | 使用强密码，至少 16 位 |
| `JWT_SECRET` | JWT 密钥 | 使用 `openssl rand -hex 32` 生成 |
| `ADMIN_PASSWORD` | 管理员密码 | 使用强密码，至少 12 位 |
| `TELEGRAM_API_ID` | Telegram API ID | 从 my.telegram.org 获取 |
| `TELEGRAM_API_HASH` | Telegram API Hash | 从 my.telegram.org 获取 |
| `DIFY_API_KEY` | Dify API 密钥 | 从 Dify 控制台获取 |

### 2.2 生成安全密钥

```bash
# 生成 JWT 密钥
openssl rand -hex 32

# 生成数据库密码
openssl rand -base64 24

# 生成管理员密码
openssl rand -base64 16
```

### 2.3 防火墙配置

```bash
# 安装 ufw（如未安装）
sudo apt install ufw

# 允许 SSH
sudo ufw allow 22

# 允许 HTTP/HTTPS
sudo ufw allow 80
sudo ufw allow 443

# 启用防火墙
sudo ufw enable
```

**注意**: 数据库端口 (5432) 和后端 API 端口 (8000) 不应暴露到公网。

## 3. 部署步骤

### 3.1 安装 Docker

```bash
# 更新系统
sudo apt update && sudo apt upgrade -y

# 安装 Docker
curl -fsSL https://get.docker.com | sh

# 安装 Docker Compose
sudo apt install docker-compose-plugin

# 将当前用户添加到 docker 组
sudo usermod -aG docker $USER

# 重新登录以生效
exit
```

### 3.2 克隆项目

```bash
# 克隆仓库
git clone https://github.com/reportyao/tezbarakat-telegram-bot.git
cd tezbarakat-telegram-bot

# 创建必要的目录
mkdir -p sessions logs
chmod 755 sessions logs
```

### 3.3 配置环境变量

```bash
# 复制环境变量模板
cp .env.example .env

# 编辑配置（参考上面的安全配置清单）
nano .env
```

### 3.4 启动服务

```bash
# 构建并启动所有服务
docker compose up -d --build

# 查看服务状态
docker compose ps

# 查看日志
docker compose logs -f
```

### 3.5 验证部署

```bash
# 检查服务健康状态
curl http://localhost/health

# 检查前端是否可访问
curl http://localhost/
```

## 4. SSL/HTTPS 配置

### 4.1 使用 Let's Encrypt（推荐）

```bash
# 安装 certbot
sudo apt install certbot

# 获取证书（替换为您的域名）
sudo certbot certonly --standalone -d your-domain.com

# 证书位置
# /etc/letsencrypt/live/your-domain.com/fullchain.pem
# /etc/letsencrypt/live/your-domain.com/privkey.pem
```

### 4.2 配置 Nginx SSL

创建 `web_frontend/nginx-ssl.conf`:

```nginx
server {
    listen 80;
    server_name your-domain.com;
    return 301 https://$server_name$request_uri;
}

server {
    listen 443 ssl http2;
    server_name your-domain.com;

    ssl_certificate /etc/letsencrypt/live/your-domain.com/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/your-domain.com/privkey.pem;
    
    ssl_protocols TLSv1.2 TLSv1.3;
    ssl_ciphers ECDHE-ECDSA-AES128-GCM-SHA256:ECDHE-RSA-AES128-GCM-SHA256;
    ssl_prefer_server_ciphers off;

    # ... 其他配置与 nginx.conf 相同
}
```

## 5. 监控和维护

### 5.1 查看日志

```bash
# 查看所有服务日志
docker compose logs -f

# 查看特定服务日志
docker compose logs -f bot_core
docker compose logs -f web_backend

# 查看应用日志文件
tail -f logs/web_backend.log
tail -f logs/bot_core.log
```

### 5.2 备份数据

```bash
# 备份数据库
docker compose exec db pg_dump -U user tezbarakat > backup_$(date +%Y%m%d).sql

# 备份 session 文件
tar -czvf sessions_backup_$(date +%Y%m%d).tar.gz sessions/
```

### 5.3 更新部署

```bash
# 拉取最新代码
git pull origin main

# 重新构建并启动
docker compose up -d --build

# 清理旧镜像
docker image prune -f
```

### 5.4 重启服务

```bash
# 重启所有服务
docker compose restart

# 重启特定服务
docker compose restart bot_core
```

## 6. 故障排查

### 6.1 常见问题

**问题**: Bot 无法连接 Telegram
- 检查服务器是否能访问 Telegram API
- 检查 `TELEGRAM_API_ID` 和 `TELEGRAM_API_HASH` 是否正确
- 检查 session 文件是否存在

**问题**: 数据库连接失败
- 检查数据库容器是否运行: `docker compose ps db`
- 检查数据库日志: `docker compose logs db`
- 检查 `DATABASE_URL` 配置是否正确

**问题**: 前端无法访问 API
- 检查 Nginx 配置是否正确
- 检查后端服务是否运行: `docker compose ps web_backend`
- 检查 CORS 配置

### 6.2 健康检查

```bash
# 检查所有服务健康状态
docker compose ps

# 检查后端 API
curl http://localhost:8000/health

# 检查 Bot 核心服务
curl http://localhost:8001/health
```

## 7. 安全建议

1. **定期更新**: 定期更新系统和 Docker 镜像
2. **密码轮换**: 定期更换管理员密码和 JWT 密钥
3. **日志审计**: 定期检查日志，发现异常行为
4. **备份策略**: 每日备份数据库，保留至少 7 天
5. **访问控制**: 限制管理后台的访问 IP
6. **监控告警**: 配置服务监控和告警通知

## 8. 联系支持

如有问题，请提交 Issue 或联系技术支持。
