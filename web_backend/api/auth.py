"""
Tezbarakat Telegram Bot - 认证和 Bot 控制 API
"""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from datetime import timedelta

import sys
sys.path.append('..')
from models.database import get_db
from models.schemas import (
    LoginRequest, TokenResponse, BaseResponse,
    BotStatus, BotControlRequest
)
from services.auth_service import (
    authenticate_admin, create_access_token, get_current_user
)
from config import settings

router = APIRouter(tags=["认证"])


@router.post("/auth/login", response_model=TokenResponse)
async def login(login_request: LoginRequest):
    """管理员登录"""
    if not authenticate_admin(login_request.username, login_request.password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="用户名或密码错误",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    access_token_expires = timedelta(minutes=settings.access_token_expire_minutes)
    access_token = create_access_token(
        data={"sub": login_request.username},
        expires_delta=access_token_expires
    )
    
    return TokenResponse(
        access_token=access_token,
        token_type="bearer",
        expires_in=settings.access_token_expire_minutes * 60
    )


@router.post("/auth/logout", response_model=BaseResponse)
async def logout(current_user: dict = Depends(get_current_user)):
    """登出（客户端需要清除 token）"""
    return BaseResponse(success=True, message="登出成功")


@router.get("/auth/me")
async def get_current_user_info(current_user: dict = Depends(get_current_user)):
    """获取当前用户信息"""
    return current_user


# =====================================================
# Bot 控制
# =====================================================

@router.get("/bot/status", response_model=BotStatus)
async def get_bot_status(
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """获取 Bot 运行状态"""
    from ..utils.bot_manager import bot_manager
    
    status_info = bot_manager.get_status()
    
    return BotStatus(
        running=status_info['running'],
        uptime=status_info.get('uptime'),
        connected_accounts=status_info.get('connected_accounts', 0),
        monitored_groups=status_info.get('monitored_groups', 0),
        last_message_time=status_info.get('last_message_time')
    )


@router.post("/bot/control", response_model=BaseResponse)
async def control_bot(
    control: BotControlRequest,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """控制 Bot 启动/停止/重启"""
    from ..utils.bot_manager import bot_manager
    
    try:
        if control.action == 'start':
            await bot_manager.start()
            return BaseResponse(success=True, message="Bot 已启动")
        elif control.action == 'stop':
            await bot_manager.stop()
            return BaseResponse(success=True, message="Bot 已停止")
        elif control.action == 'restart':
            await bot_manager.restart()
            return BaseResponse(success=True, message="Bot 已重启")
        else:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="无效的操作"
            )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"操作失败: {str(e)}"
        )


@router.post("/bot/test-dify", response_model=BaseResponse)
async def test_dify_connection(
    current_user: dict = Depends(get_current_user)
):
    """测试 Dify 连接"""
    from ..utils.bot_manager import bot_manager
    
    try:
        success, message = await bot_manager.test_dify_connection()
        return BaseResponse(success=success, message=message)
    except Exception as e:
        return BaseResponse(success=False, message=f"测试失败: {str(e)}")
