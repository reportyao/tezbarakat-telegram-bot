"""
Tezbarakat Telegram Bot - Bot 核心服务主入口
"""

import sys
import os
import asyncio
from datetime import datetime, timedelta
from typing import Optional

# 添加项目根目录到路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from fastapi import FastAPI, HTTPException, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from contextlib import asynccontextmanager
from loguru import logger
import uvicorn
import pytz

from config import bot_settings
from services.telegram_client import client_manager
from services.dify_service import dify_service
from services.database import db_service
from handlers.message_handler import message_handler


# 配置日志
os.makedirs(bot_settings.log_path, exist_ok=True)
logger.add(
    f"{bot_settings.log_path}/bot_core.log",
    rotation="10 MB",
    retention="7 days",
    level=bot_settings.log_level,
    format="{time:YYYY-MM-DD HH:mm:ss} | {level} | {module}:{function}:{line} | {message}"
)


# 全局状态
class BotState:
    running: bool = False
    start_time: Optional[datetime] = None
    health_check_task: Optional[asyncio.Task] = None
    reset_task: Optional[asyncio.Task] = None


bot_state = BotState()


async def load_config_from_db():
    """从数据库加载配置"""
    try:
        configs = await db_service.get_all_configs()
        
        # 更新 bot_settings
        for key, value in configs.items():
            if hasattr(bot_settings, key):
                # 处理 JSONB 值
                if isinstance(value, str):
                    try:
                        import json
                        value = json.loads(value)
                    except (json.JSONDecodeError, ValueError):
                        pass  # 保持原始字符串值
                setattr(bot_settings, key, value)
        
        # 重新加载 Dify 服务配置
        dify_service.reload_config()
        
        logger.info("已从数据库加载配置")
    except Exception as e:
        logger.error(f"从数据库加载配置失败: {e}")


async def start_bot():
    """启动 Bot"""
    if bot_state.running:
        logger.warning("Bot 已经在运行中")
        return
    
    logger.info("正在启动 Bot 核心服务...")
    
    try:
        # 从数据库加载配置
        await load_config_from_db()
        
        # 初始化消息处理器
        await message_handler.initialize()
        
        # 加载并连接所有账号
        accounts = await db_service.get_all_accounts()
        
        for account in accounts:
            # 使用 ORM 对象属性访问
            status = account.status if hasattr(account, 'status') else account.get('status', '')
            phone_number = account.phone_number if hasattr(account, 'phone_number') else account.get('phone_number', '')
            session_name = account.session_name if hasattr(account, 'session_name') else account.get('session_name', '')
            
            if status in ['active', 'logging_in']:
                try:
                    success = await client_manager.connect_existing(
                        phone=phone_number,
                        session_name=session_name
                    )
                    if success:
                        logger.info(f"账号 {phone_number} 连接成功")
                        
                        # 获取并记录账号的用户 ID
                        user_id = await client_manager.get_user_id(phone_number)
                        if user_id:
                            message_handler.add_our_user_id(user_id)
                            logger.debug(f"已记录账号 {phone_number} 的用户 ID: {user_id}")
                    else:
                        logger.warning(f"账号 {phone_number} 连接失败")
                        await db_service.update_account_status(phone_number, 'limited')
                except Exception as e:
                    logger.error(f"连接账号 {phone_number} 时出错: {e}")
        
        # 设置主监听账号（第一个活跃账号）
        active_phones = client_manager.active_phones
        if active_phones:
            client_manager.set_main_client(active_phones[0])
        
        # 启动健康检查任务
        bot_state.health_check_task = asyncio.create_task(health_check_loop())
        
        # 启动定时重置任务
        bot_state.reset_task = asyncio.create_task(reset_counters_loop())
        
        bot_state.running = True
        bot_state.start_time = datetime.now()
        
        logger.info(f"Bot 核心服务已启动，连接了 {client_manager.connected_count} 个账号")
        
    except Exception as e:
        logger.error(f"启动 Bot 失败: {e}", exc_info=True)
        raise


async def stop_bot():
    """停止 Bot"""
    if not bot_state.running:
        logger.warning("Bot 未在运行")
        return
    
    logger.info("正在停止 Bot 核心服务...")
    
    try:
        # 取消健康检查任务
        if bot_state.health_check_task:
            bot_state.health_check_task.cancel()
            try:
                await bot_state.health_check_task
            except asyncio.CancelledError:
                pass
        
        # 取消重置任务
        if bot_state.reset_task:
            bot_state.reset_task.cancel()
            try:
                await bot_state.reset_task
            except asyncio.CancelledError:
                pass
        
        # 断开所有连接
        await client_manager.disconnect_all()
        
        # 关闭数据库连接
        await db_service.close_session()
        
        bot_state.running = False
        bot_state.start_time = None
        
        logger.info("Bot 核心服务已停止")
        
    except Exception as e:
        logger.error(f"停止 Bot 时出错: {e}", exc_info=True)


async def health_check_loop():
    """健康检查循环"""
    while True:
        try:
            await asyncio.sleep(3600)  # 每小时检查一次
            
            if not bot_state.running:
                break
            
            logger.info("执行账号健康检查...")
            
            for phone in client_manager.active_phones:
                is_healthy, message = await client_manager.check_account_health(phone)
                
                if not is_healthy:
                    logger.warning(f"账号 {phone} 健康检查失败: {message}")
                    await db_service.update_account_status(phone, 'limited')
                    
                    # 创建告警
                    await db_service.create_alert(
                        alert_type='account_health',
                        title=f'账号健康检查失败',
                        message=f'账号 {phone}: {message}',
                        severity='warning'
                    )
                    
        except asyncio.CancelledError:
            break
        except Exception as e:
            logger.error(f"健康检查出错: {e}")


async def reset_counters_loop():
    """定时重置计数器循环"""
    tz = pytz.timezone(bot_settings.timezone)
    
    while True:
        try:
            now = datetime.now(tz)
            
            # 计算到下一个整点的秒数
            next_hour = (now + timedelta(hours=1)).replace(minute=0, second=0, microsecond=0)
            sleep_seconds = (next_hour - now).total_seconds()
            
            await asyncio.sleep(sleep_seconds)
            
            if not bot_state.running:
                break
            
            current_hour = datetime.now(tz).hour
            
            # 每小时重置群组回复计数
            logger.info("重置群组每小时回复计数...")
            await db_service.reset_hourly_group_counts()
            
            # 每天凌晨重置账号每日消息计数
            if current_hour == 0:
                logger.info("重置账号每日消息计数...")
                await db_service.reset_daily_account_counts()
                
                # 恢复 cooling_down 状态的账号
                logger.info("恢复冷却中的账号...")
                await db_service.recover_cooling_accounts()
            
        except asyncio.CancelledError:
            break
        except Exception as e:
            logger.error(f"重置计数器出错: {e}")


@asynccontextmanager
async def lifespan(app: FastAPI):
    """应用生命周期管理"""
    logger.info("Bot 核心服务 API 启动中...")
    
    # 加载数据库中已有的账号
    try:
        accounts = await db_service.get_all_accounts()
        logger.info(f"从数据库加载到 {len(accounts)} 个账号")
        
        for account in accounts:
            if account.status == 'active':
                phone = account.phone_number
                session_name = account.session_name
                
                logger.info(f"尝试连接账号: {phone} (session: {session_name})")
                try:
                    success = await client_manager.connect_existing(phone, session_name)
                    if success:
                        logger.info(f"账号 {phone} 连接成功")
                        # 记录用户 ID
                        user_id = await client_manager.get_user_id(phone)
                        if user_id:
                            message_handler.add_our_user_id(user_id)
                    else:
                        logger.warning(f"账号 {phone} 连接失败")
                except Exception as e:
                    logger.error(f"连接账号 {phone} 时出错: {e}")
    except Exception as e:
        logger.error(f"加载账号失败: {e}")
    
    yield
    logger.info("Bot 核心服务 API 关闭中...")
    await stop_bot()


# 创建 FastAPI 应用
app = FastAPI(
    title="Tezbarakat Bot Core API",
    version="1.0.0",
    description="Bot 核心服务内部 API",
    lifespan=lifespan
)

# 配置 CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# =====================================================
# API 模型
# =====================================================

class LoginStartRequest(BaseModel):
    phone: str
    session_name: str


class LoginCompleteRequest(BaseModel):
    phone: str
    code: Optional[str] = None
    password: Optional[str] = None


class GroupRequest(BaseModel):
    group_id: int


class ReconnectRequest(BaseModel):
    phone: str
    session_name: str


# =====================================================
# API 端点
# =====================================================

@app.get("/health")
async def health():
    """健康检查"""
    return {
        "status": "healthy",
        "running": bot_state.running,
        "connected_accounts": client_manager.connected_count
    }


@app.post("/start")
async def api_start_bot(background_tasks: BackgroundTasks):
    """启动 Bot"""
    if bot_state.running:
        return {"status": "already_running"}
    
    background_tasks.add_task(start_bot)
    return {"status": "starting"}


@app.post("/stop")
async def api_stop_bot():
    """停止 Bot"""
    if not bot_state.running:
        return {"status": "not_running"}
    
    await stop_bot()
    return {"status": "stopped"}


@app.get("/status")
async def get_status():
    """获取状态"""
    uptime = None
    if bot_state.start_time and bot_state.running:
        uptime = int((datetime.now() - bot_state.start_time).total_seconds())
    
    return {
        "running": bot_state.running,
        "uptime": uptime,
        "connected_accounts": client_manager.connected_count,
        "monitored_groups": len(message_handler._monitored_groups),
        "keywords_count": len(message_handler._keywords)
    }


# =====================================================
# 账号管理 API
# =====================================================

@app.post("/accounts/login/start")
async def start_login(request: LoginStartRequest):
    """开始登录"""
    try:
        result = await client_manager.start_login(request.phone, request.session_name)
        return result
    except Exception as e:
        logger.error(f"开始登录失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/accounts/login/complete")
async def complete_login(request: LoginCompleteRequest):
    """完成登录"""
    try:
        result = await client_manager.complete_login(
            request.phone,
            code=request.code,
            password=request.password
        )
        
        # 如果登录成功，记录用户 ID
        if result.get('success'):
            user_id = await client_manager.get_user_id(request.phone)
            if user_id:
                message_handler.add_our_user_id(user_id)
        
        return result
    except Exception as e:
        logger.error(f"完成登录失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.delete("/accounts/{phone}")
async def remove_account(phone: str):
    """移除账号"""
    await client_manager.disconnect(phone)
    return {"status": "removed"}


@app.post("/accounts/reconnect")
async def reconnect_account(request: ReconnectRequest):
    """重新连接账号"""
    try:
        success = await client_manager.connect_existing(request.phone, request.session_name)
        if success:
            # 记录用户 ID
            user_id = await client_manager.get_user_id(request.phone)
            if user_id:
                message_handler.add_our_user_id(user_id)
            return {"status": "connected"}
        else:
            raise HTTPException(status_code=400, detail="连接失败")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/accounts/{phone}/health")
async def check_account_health(phone: str):
    """检查账号健康"""
    is_healthy, message = await client_manager.check_account_health(phone)
    return {"healthy": is_healthy, "message": message}


# =====================================================
# 群组管理 API
# =====================================================

@app.get("/groups/resolve")
async def resolve_group(username: str):
    """解析群组"""
    result = await client_manager.resolve_username(username)
    if result:
        return result
    raise HTTPException(status_code=404, detail="未找到群组")


@app.get("/groups/{group_id}/info")
async def get_group_info(group_id: int):
    """获取群组信息"""
    result = await client_manager.get_entity_info(group_id)
    if result:
        return result
    raise HTTPException(status_code=404, detail="未找到群组")


@app.post("/groups/add")
async def add_group(request: GroupRequest):
    """添加群组"""
    message_handler.add_group(request.group_id)
    return {"status": "added"}


@app.post("/groups/remove")
async def remove_group(request: GroupRequest):
    """移除群组"""
    message_handler.remove_group(request.group_id)
    return {"status": "removed"}


# =====================================================
# 关键词和配置 API
# =====================================================

@app.post("/keywords/reload")
async def reload_keywords():
    """重新加载关键词"""
    await message_handler.reload_keywords()
    return {"status": "reloaded", "count": len(message_handler._keywords)}


@app.post("/config/reload")
async def reload_config():
    """重新加载配置"""
    await load_config_from_db()
    return {"status": "reloaded"}


# =====================================================
# Dify API
# =====================================================

@app.get("/dify/test")
async def test_dify():
    """测试 Dify 连接"""
    success, message = await dify_service.test_connection()
    return {"success": success, "message": message}


if __name__ == "__main__":
    uvicorn.run(
        "main:app",
        host=bot_settings.api_host,
        port=bot_settings.api_port,
        reload=False,
        log_level=bot_settings.log_level.lower()
    )
