# AI 客服 Bot (Dify 集成版)

这是一个独立的 Telegram Bot 服务，用于处理客服消息并通过 Dify AI 平台提供智能回复。

## 功能特性

- **私聊消息处理**: 直接与用户进行一对一对话
- **Business 消息转发**: 支持 Telegram Business 功能，处理个人号消息
- **群组 @Bot 消息响应**: 在群组中被 @ 时自动回复
- **新人入群欢迎**: 自动发送欢迎消息给新加入群组的成员

## 技术特点

- **异步 API 调用**: 使用 `httpx` 实现非阻塞的 Dify API 调用
- **日志轮转**: 使用 `TimedRotatingFileHandler` 自动管理日志文件
- **错误处理增强**: 针对不同类型的错误提供友好的用户提示
- **消息处理器优化**: 修复了处理器顺序和过滤器逻辑

## 配置说明

主要配置项在 `bot.py` 文件顶部:

```python
TELEGRAM_BOT_TOKEN = "your_bot_token"
DIFY_API_URL = "http://localhost:3001/v1/chat-messages"
DIFY_API_KEY = "your_dify_api_key"
```

## 群组配置

可以为不同群组配置不同的欢迎消息和邀请链接:

```python
GROUP_CONFIGS = {
    -1001234567890: {
        "name": "群组名称",
        "invite_code": "INVITE_CODE",
        "miniapp_url": "https://t.me/yourbot/app?startapp=CODE",
        "materials_url": "https://your-materials-url.com/"
    },
    "default": {
        # 默认配置
    }
}
```

## 运行方式

使用 PM2 管理:

```bash
pm2 start bot.py --name tg-ai-bot --interpreter python3
```

## 依赖

- python-telegram-bot
- httpx
- loguru (可选)

## 更新日志

### v1.1.0 (2026-02-03)

**Bug 修复:**
- 修复消息处理器顺序错误导致的逻辑混乱
- 优化 Dify API 错误处理，提供更友好的错误提示
- 改进群组 @Bot 检测逻辑

**优化:**
- 使用 httpx 实现异步 API 调用，提升并发性能
- 添加日志轮转功能，自动管理日志文件
- 增强错误分类和用户提示
