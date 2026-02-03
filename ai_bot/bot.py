#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Telegram Bot - 完整版 (修复优化版)
功能：
1. 私聊消息处理
2. Business 消息转发（个人号 @Tezbarakat_Malika）
3. 群组 @Bot 消息响应
4. 新人入群欢迎

修复内容：
- Bug 1: 修复消息处理器顺序和逻辑
- Bug 2: 优化API错误处理，提供更友好的错误提示
- Bug 3: 改进日志记录
- 优化3: 使用httpx实现异步API调用
"""

import logging
from logging.handlers import TimedRotatingFileHandler
import httpx
import time
import asyncio
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, WebAppInfo
from telegram.ext import (
    Application,
    MessageHandler,
    filters,
    ContextTypes,
)

# ==================== 配置 ====================
TELEGRAM_BOT_TOKEN = "8505618130:AAEnyJj9pIMr9Ew6FsBlPLKBtXPFSTA9EFo"
DIFY_API_URL = "http://localhost:3001/v1/chat-messages"
DIFY_API_KEY = "app-oyycYVetPyt58JalkHF2qEpv"

# ==================== 群组配置 ====================
# 为不同群组配置不同的欢迎消息和邀请链接
GROUP_CONFIGS = {
    # 示例配置（请根据实际群组ID修改）
    # -1001234567890: {
    #     "name": "推广员A的群",
    #     "invite_code": "AGENT_A_CODE",
    #     "miniapp_url": "https://t.me/tezbarakatbot/shoppp?startapp=AGENT_A_CODE",
    #     "materials_url": "https://earn.tezbarakat.com/"
    # },
    
    # 默认配置（当群组ID不在上面列表中时使用）
    "default": {
        "name": "TezBarakat官方群",
        "invite_code": "LMBDZU9A",
        "miniapp_url": "https://t.me/tezbarakatbot/shoppp?startapp=LMBDZU9A",
        "materials_url": "https://earn.tezbarakat.com/"
    }
}

# 新人欢迎文案模板（塔吉克语）
WELCOME_MESSAGE_TEMPLATE = """🎉 Хуш омадед ба TezBarakat!

Мо платформаи тиҷорати иҷтимоӣ барои Тоҷикистон ҳастем. Дар ин ҷо шумо метавонед:

✅ Маҳсулот харида, пул даромад кунед
💰 Аз системаи 3-сатҳӣ даромад гиред (5%-3%-1%)
🎁 Бо дӯстон мубодила кунед ва пурра гиред

🛍 Платформаро кушоед ва материалҳоро бинед:

❓ Саволҳо доред? @Tezbarakat_Malikabot-ро пурсед!"""

# 获取群组配置
def get_group_config(chat_id):
    """根据群组ID获取配置，如果不存在则返回默认配置"""
    return GROUP_CONFIGS.get(chat_id, GROUP_CONFIGS["default"])

# ==================== 日志配置 (优化: 日志轮转) ====================
log_file = '/root/ai_bot/bot.log'
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

# 创建格式化器
formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')

# 创建一个按天轮转的处理器，保留7天日志
file_handler = TimedRotatingFileHandler(
    log_file, 
    when="midnight", 
    interval=1, 
    backupCount=7, 
    encoding='utf-8'
)
file_handler.setFormatter(formatter)

# 控制台处理器
console_handler = logging.StreamHandler()
console_handler.setFormatter(formatter)

# 添加处理器
logger.addHandler(file_handler)
logger.addHandler(console_handler)

# ==================== Dify API 调用 (优化3: 异步化) ====================
async def call_dify_api(user_message: str, user_id: int) -> str:
    """异步调用 Dify API 获取回复"""
    try:
        start_time = time.time()
        
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.post(
                DIFY_API_URL,
                json={
                    "inputs": {},
                    "query": user_message,
                    "response_mode": "blocking",
                    "user": str(user_id)
                },
                headers={
                    "Authorization": f"Bearer {DIFY_API_KEY}",
                    "Content-Type": "application/json"
                }
            )
        
        elapsed = time.time() - start_time
        
        if response.status_code == 200:
            data = response.json()
            answer = data.get("answer", "抱歉，我现在无法回答这个问题。")
            logger.info(f"[AI生成] 用户: {user_id} | 耗时: {elapsed:.2f}s | 回复长度: {len(answer)}")
            return answer
        else:
            error_text = response.text
            logger.error(f"[Dify API错误] 状态码: {response.status_code} | 响应: {error_text}")
            # Bug 2 修复: 根据错误内容返回更具体的提示
            if "Read timed out" in error_text or "completion_request_error" in error_text:
                return "抱歉，AI模型正在思考中，请稍等片刻再试一次。"
            elif "500 Internal Server Error" in error_text:
                return "抱歉，服务器内部出现问题，请稍后再试。"
            else:
                return "抱歉，服务暂时不可用，请稍后再试。"
            
    except httpx.TimeoutException:
        logger.error(f"[Dify API超时] 用户: {user_id}")
        return "抱歉，AI模型响应超时，请稍等片刻再试一次。"
    except httpx.ConnectError:
        logger.error(f"[Dify API连接失败] 用户: {user_id}")
        return "抱歉，无法连接到AI服务，请稍后再试。"
    except Exception as e:
        logger.error(f"[Dify API异常] 用户: {user_id} | 错误: {str(e)}")
        return "抱歉，服务出现异常，请稍后再试。"

# ==================== Business 消息处理 ====================
async def handle_business_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """处理 Business 消息（个人号转发）"""
    try:
        message = update.business_message
        if not message or not message.text:
            return
        
        user = message.from_user
        user_id = user.id
        username = user.username or "Unknown"
        first_name = user.first_name or ""
        last_name = user.last_name or ""
        full_name = f"{first_name} {last_name}".strip() or username
        
        user_message = message.text
        
        logger.info(f"[Business消息] 用户: {full_name} (@{username}) | ID: {user_id}")
        logger.info(f"[消息内容] {user_message}")
        
        # 异步调用 Dify API
        reply = await call_dify_api(user_message, user_id)
        
        # 发送回复
        try:
            # 获取 business_connection_id
            business_connection_id = None
            if hasattr(update, 'business_connection') and update.business_connection:
                business_connection_id = update.business_connection.id
            elif hasattr(message, 'business_connection_id'):
                business_connection_id = message.business_connection_id
            
            if not business_connection_id:
                logger.error("[Business回复失败] 无法获取 business_connection_id")
                return
            
            await context.bot.send_message(
                business_connection_id=business_connection_id,
                chat_id=message.chat.id,
                text=reply
            )
            logger.info(f"[Business回复成功] 用户: {user_id}")
        except Exception as send_error:
            logger.error(f"[Business回复失败] 错误: {str(send_error)}")
        
    except Exception as e:
        logger.error(f"[Business消息处理失败] 错误: {str(e)}")

# ==================== 私聊消息处理 ====================
async def handle_direct_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """处理直接私聊消息"""
    try:
        message = update.message
        if not message or not message.text:
            return
        
        user = message.from_user
        user_id = user.id
        username = user.username or "Unknown"
        first_name = user.first_name or ""
        last_name = user.last_name or ""
        full_name = f"{first_name} {last_name}".strip() or username
        
        user_message = message.text
        
        logger.info(f"[收到消息] 用户: {full_name} (@{username}) | ID: {user_id}")
        logger.info(f"[消息内容] {user_message}")
        
        # 异步调用 Dify API
        reply = await call_dify_api(user_message, user_id)
        
        # 发送回复
        await message.reply_text(reply)
        
        logger.info(f"[回复成功] 用户: {user_id}")
        
    except Exception as e:
        logger.error(f"[消息处理失败] 错误: {str(e)}")

# ==================== 群组消息处理 (Bug 1 修复: 优化@检测逻辑) ====================
async def handle_group_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """处理群组中@Bot的消息"""
    try:
        message = update.message
        if not message or not message.text:
            return
        
        # 检查是否在群组中
        if message.chat.type not in ['group', 'supergroup']:
            return
        
        # 检查是否@了Bot
        bot_username = context.bot.username
        mentioned = False
        
        # 方法1：检查 entities 中的 mention
        if message.entities:
            for entity in message.entities:
                if entity.type == 'mention':
                    mention_text = message.text[entity.offset:entity.offset + entity.length]
                    if f"@{bot_username}" in mention_text:
                        mentioned = True
                        break
                elif entity.type == 'text_mention':
                    if entity.user and entity.user.id == context.bot.id:
                        mentioned = True
                        break
        
        # 方法2：检查文本中是否包含@Bot（大小写不敏感）
        if not mentioned and f"@{bot_username}".lower() in message.text.lower():
            mentioned = True
        
        # Bug 1 修复: 如果没有被@，直接返回，不做任何处理
        if not mentioned:
            return
        
        user = message.from_user
        user_id = user.id
        username = user.username or "Unknown"
        first_name = user.first_name or ""
        last_name = user.last_name or ""
        full_name = f"{first_name} {last_name}".strip() or username
        
        # 移除@Bot的部分，获取纯净的用户消息（大小写不敏感替换）
        import re
        user_message = re.sub(rf'@{bot_username}', '', message.text, flags=re.IGNORECASE).strip()
        
        # 如果移除@后消息为空，给一个默认提示
        if not user_message:
            user_message = "你好"
        
        logger.info(f"[群组消息] 群: {message.chat.title} | 用户: {full_name} (@{username}) | ID: {user_id}")
        logger.info(f"[消息内容] {user_message}")
        
        # 异步调用 Dify API
        reply = await call_dify_api(user_message, user_id)
        
        # 在群组中回复
        await message.reply_text(reply)
        
        logger.info(f"[群组回复成功] 用户: {user_id}")
        
    except Exception as e:
        logger.error(f"[群组消息处理失败] 错误: {str(e)}")

# ==================== 新人入群欢迎 ====================
async def welcome_new_member(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """处理新成员加入群组"""
    try:
        message = update.message
        if not message or not message.new_chat_members:
            return
        
        # 为每个新成员发送欢迎消息
        for new_member in message.new_chat_members:
            # 跳过 Bot 自己
            if new_member.id == context.bot.id:
                logger.info(f"[Bot加入群组] 群: {message.chat.title}")
                continue
            
            username = new_member.username or "Unknown"
            first_name = new_member.first_name or ""
            last_name = new_member.last_name or ""
            full_name = f"{first_name} {last_name}".strip() or username
            
            # 获取群组配置
            chat_id = message.chat.id
            group_config = get_group_config(chat_id)
            
            logger.info(f"[新成员入群] 群: {message.chat.title} (ID: {chat_id}) | 新成员: {full_name} (@{username})")
            logger.info(f"[使用配置] {group_config['name']} | 邀请码: {group_config['invite_code']}")
            
            # 创建按钮（使用群组配置的链接）
            keyboard = [
                [InlineKeyboardButton(
                    "🚀 Кушодани TezBarakat", 
                    web_app=WebAppInfo(url=group_config['miniapp_url'])
                )],
                [InlineKeyboardButton(
                    "📚 Китобхонаи маводҳо", 
                    url=group_config['materials_url']
                )]
            ]
            reply_markup = InlineKeyboardMarkup(keyboard)
            
            # 发送欢迎消息
            await message.reply_text(
                WELCOME_MESSAGE_TEMPLATE,
                reply_markup=reply_markup
            )
            
            logger.info(f"[欢迎消息已发送] 新成员: {full_name}")
        
    except Exception as e:
        logger.error(f"[欢迎消息发送失败] 错误: {str(e)}")

# ==================== Dify 连接测试 (优化: 异步化) ====================
async def test_dify_connection():
    """启动时测试 Dify 连接"""
    try:
        logger.info("[启动检查] 测试 Dify API 连接...")
        start_time = time.time()
        
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.post(
                DIFY_API_URL,
                json={
                    "inputs": {},
                    "query": "你好",
                    "response_mode": "blocking",
                    "user": "system_test"
                },
                headers={
                    "Authorization": f"Bearer {DIFY_API_KEY}",
                    "Content-Type": "application/json"
                }
            )
        
        elapsed = time.time() - start_time
        
        if response.status_code == 200:
            data = response.json()
            answer = data.get("answer", "")
            logger.info(f"[Dify连接成功] 耗时: {elapsed:.2f}s | 回复: {answer[:50]}...")
            return True
        else:
            logger.error(f"[Dify连接失败] 状态码: {response.status_code}")
            return False
            
    except Exception as e:
        logger.error(f"[Dify连接异常] 错误: {str(e)}")
        return False

# ==================== 主函数 ====================
def main():
    """主函数"""
    logger.info("=" * 60)
    logger.info("Telegram Bot 启动中... (修复优化版)")
    logger.info("功能: 私聊、Business消息、群组@消息、新人欢迎")
    logger.info("优化: 异步API调用、日志轮转、错误处理增强")
    logger.info("=" * 60)
    
    # 创建 Application
    application = Application.builder().token(TELEGRAM_BOT_TOKEN).build()
    
    # 在启动前测试 Dify 连接
    async def post_init(app):
        if not await test_dify_connection():
            logger.warning("[警告] Dify API 连接测试失败，但 Bot 将继续启动")
    
    application.post_init = post_init
    
    # 添加消息处理器（按优先级顺序）
    # Bug 1 修复: 调整处理器顺序和过滤器
    
    # 1. 新人入群欢迎处理器（最高优先级）
    application.add_handler(MessageHandler(
        filters.StatusUpdate.NEW_CHAT_MEMBERS,
        welcome_new_member
    ))
    
    # 2. Business 消息处理器
    application.add_handler(MessageHandler(
        filters.UpdateType.BUSINESS_MESSAGE & filters.TEXT & ~filters.COMMAND,
        handle_business_message
    ))
    
    # 3. 私聊消息处理器 (放在群组处理器之前)
    application.add_handler(MessageHandler(
        filters.ChatType.PRIVATE & filters.TEXT & ~filters.COMMAND,
        handle_direct_message
    ))
    
    # 4. 群组消息处理器（包含@Bot的消息）
    # Bug 1 修复: 使用 filters.Mention 来更精确地过滤@消息
    application.add_handler(MessageHandler(
        (filters.ChatType.GROUPS | filters.ChatType.SUPERGROUP) & filters.TEXT & ~filters.COMMAND,
        handle_group_message
    ))
    
    logger.info("[Bot已启动] 开始监听消息...")
    logger.info("[支持类型] 私聊、Business消息、群组@消息、新人欢迎")
    logger.info("[群组配置] 已配置 " + str(len([k for k in GROUP_CONFIGS.keys() if k != 'default'])) + " 个群组")
    logger.info("[默认配置] " + GROUP_CONFIGS['default']['name'] + " | 邀请码: " + GROUP_CONFIGS['default']['invite_code'])
    
    # 启动 Bot
    application.run_polling(allowed_updates=Update.ALL_TYPES, drop_pending_updates=False)

if __name__ == "__main__":
    main()
