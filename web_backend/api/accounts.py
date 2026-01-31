"""
Tezbarakat Telegram Bot - 账号管理 API
"""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Optional
import re

import sys
sys.path.append('..')
from models.database import get_db
from models.schemas import (
    AccountCreate, AccountLogin, AccountResponse, AccountStatusUpdate,
    AccountListResponse, BaseResponse
)
from services.db_service import DatabaseService
from services.auth_service import get_current_user

router = APIRouter(prefix="/accounts", tags=["账号管理"])


def validate_phone_number(phone: str) -> str:
    """验证并标准化手机号"""
    # 移除所有非数字字符（除了开头的+）
    if phone.startswith('+'):
        cleaned = '+' + re.sub(r'\D', '', phone[1:])
    else:
        cleaned = re.sub(r'\D', '', phone)
    
    # 确保有国际区号
    if not cleaned.startswith('+'):
        # 假设是塔吉克斯坦号码
        if cleaned.startswith('992'):
            cleaned = '+' + cleaned
        else:
            cleaned = '+992' + cleaned
    
    return cleaned


@router.get("", response_model=AccountListResponse)
async def get_accounts(
    status: Optional[str] = None,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """获取所有账号列表"""
    service = DatabaseService(db)
    accounts = await service.get_all_accounts(status=status)
    
    return AccountListResponse(
        total=len(accounts),
        accounts=[AccountResponse.model_validate(a) for a in accounts]
    )


@router.post("", response_model=AccountResponse)
async def create_account(
    account: AccountCreate,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """创建新账号（第一步：发送验证码）"""
    service = DatabaseService(db)
    
    # 验证手机号格式
    phone = validate_phone_number(account.phone_number)
    
    # 检查是否已存在
    existing = await service.get_account_by_phone(phone)
    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="该手机号已存在"
        )
    
    # 生成 session 名称
    session_name = f"session_{phone.replace('+', '')}"
    
    # 创建账号记录
    new_account = await service.create_account(phone, session_name)
    
    # 触发 Bot 核心服务开始登录流程
    from ..utils.bot_manager import bot_manager
    try:
        await bot_manager.start_login(phone, session_name)
    except Exception as e:
        # 如果启动登录失败，删除账号记录
        await service.delete_account(new_account.id)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"启动登录流程失败: {str(e)}"
        )
    
    return AccountResponse.model_validate(new_account)


@router.post("/login", response_model=BaseResponse)
async def complete_login(
    login_data: AccountLogin,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """完成账号登录（第二步：提交验证码/密码）"""
    service = DatabaseService(db)
    
    phone = validate_phone_number(login_data.phone_number)
    account = await service.get_account_by_phone(phone)
    
    if not account:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="账号不存在"
        )
    
    if account.status != 'logging_in':
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"账号状态不正确: {account.status}"
        )
    
    # 调用 Bot 核心服务完成登录
    from ..utils.bot_manager import bot_manager
    try:
        success = await bot_manager.complete_login(
            phone,
            code=login_data.code,
            password=login_data.password
        )
        
        if success:
            await service.update_account_status(account.id, 'active')
            return BaseResponse(success=True, message="登录成功")
        else:
            return BaseResponse(success=False, message="登录失败，请检查验证码或密码")
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"登录过程出错: {str(e)}"
        )


@router.get("/{account_id}", response_model=AccountResponse)
async def get_account(
    account_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """获取单个账号详情"""
    service = DatabaseService(db)
    account = await service.get_account_by_id(account_id)
    
    if not account:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="账号不存在"
        )
    
    return AccountResponse.model_validate(account)


@router.put("/{account_id}/status", response_model=AccountResponse)
async def update_account_status(
    account_id: int,
    status_update: AccountStatusUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """更新账号状态"""
    service = DatabaseService(db)
    account = await service.update_account_status(account_id, status_update.status)
    
    if not account:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="账号不存在"
        )
    
    return AccountResponse.model_validate(account)


@router.delete("/{account_id}", response_model=BaseResponse)
async def delete_account(
    account_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """删除账号"""
    service = DatabaseService(db)
    
    # 先获取账号信息
    account = await service.get_account_by_id(account_id)
    if not account:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="账号不存在"
        )
    
    # 从 Bot 管理器中移除
    from ..utils.bot_manager import bot_manager
    await bot_manager.remove_account(account.phone_number)
    
    # 删除数据库记录
    success = await service.delete_account(account_id)
    
    if success:
        return BaseResponse(success=True, message="账号已删除")
    else:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="删除失败"
        )


@router.post("/{account_id}/reconnect", response_model=BaseResponse)
async def reconnect_account(
    account_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """重新连接账号"""
    service = DatabaseService(db)
    account = await service.get_account_by_id(account_id)
    
    if not account:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="账号不存在"
        )
    
    from ..utils.bot_manager import bot_manager
    try:
        success = await bot_manager.reconnect_account(account.phone_number, account.session_name)
        if success:
            await service.update_account_status(account_id, 'active')
            return BaseResponse(success=True, message="重新连接成功")
        else:
            return BaseResponse(success=False, message="重新连接失败")
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"重新连接出错: {str(e)}"
        )


@router.post("/{account_id}/check", response_model=BaseResponse)
async def check_account_health(
    account_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """检查账号健康状态"""
    service = DatabaseService(db)
    account = await service.get_account_by_id(account_id)
    
    if not account:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="账号不存在"
        )
    
    from ..utils.bot_manager import bot_manager
    try:
        is_healthy, message = await bot_manager.check_account_health(account.phone_number)
        
        if not is_healthy and account.status == 'active':
            # 更新状态
            await service.update_account_status(account_id, 'limited')
        
        return BaseResponse(success=is_healthy, message=message)
    except Exception as e:
        return BaseResponse(success=False, message=f"检查失败: {str(e)}")
