"""
Tezbarakat Telegram Bot - 群组管理 API
"""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Optional
import re

import sys
sys.path.append('..')
from models.database import get_db
from models.schemas import (
    GroupCreate, GroupUpdate, GroupResponse, GroupListResponse, BaseResponse
)
from services.db_service import DatabaseService
from services.auth_service import get_current_user

router = APIRouter(prefix="/groups", tags=["群组管理"])


def parse_group_identifier(identifier: str) -> tuple:
    """
    解析群组标识符
    支持格式:
    - 数字 ID: -1001234567890
    - 用户名: @groupname
    - 链接: https://t.me/groupname
    - 链接: https://t.me/+inviteCode
    
    返回: (group_id, username, invite_link)
    """
    identifier = identifier.strip()
    
    # 数字 ID
    if identifier.lstrip('-').isdigit():
        return int(identifier), None, None
    
    # @username 格式
    if identifier.startswith('@'):
        return None, identifier[1:], None
    
    # t.me 链接
    if 't.me/' in identifier:
        # 提取链接部分
        match = re.search(r't\.me/(?:\+)?([a-zA-Z0-9_]+)', identifier)
        if match:
            part = match.group(1)
            if identifier.find('/+') > 0:
                # 邀请链接
                return None, None, identifier
            else:
                # 用户名
                return None, part, None
    
    # 假设是用户名
    return None, identifier, None


@router.get("/resolve")
async def resolve_group(
    username: str,
    current_user: dict = Depends(get_current_user)
):
    """解析群组用户名获取信息"""
    from ..utils.bot_manager import bot_manager
    
    # 清理用户名
    username = username.strip()
    if username.startswith('@'):
        username = username[1:]
    if 't.me/' in username:
        match = re.search(r't\.me/(?:\+)?([a-zA-Z0-9_]+)', username)
        if match:
            username = match.group(1)
    
    try:
        group_info = await bot_manager.resolve_group(username)
        if group_info:
            return {
                "group_id": group_info['id'],
                "title": group_info.get('title', ''),
                "username": group_info.get('username')
            }
        else:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="无法找到该群组，请确保机器人已加入该群组"
            )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"解析群组失败: {str(e)}"
        )


@router.get("", response_model=GroupListResponse)
async def get_groups(
    active_only: bool = False,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """获取所有群组列表"""
    service = DatabaseService(db)
    groups = await service.get_all_groups(active_only=active_only)
    
    return GroupListResponse(
        total=len(groups),
        groups=[GroupResponse.model_validate(g) for g in groups]
    )


@router.post("", response_model=GroupResponse)
async def create_group(
    group: GroupCreate,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """添加新群组"""
    service = DatabaseService(db)
    
    group_id = group.group_id
    group_name = group.group_name
    group_username = group.group_username
    
    # 如果提供了用户名/链接，尝试解析
    if group_username:
        parsed_id, parsed_username, invite_link = parse_group_identifier(group_username)
        if parsed_id:
            group_id = parsed_id
        if parsed_username:
            group_username = parsed_username
    
    if not group_id and not group_username:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="必须提供群组 ID 或用户名"
        )
    
    # 如果只有用户名，尝试通过 Bot 获取群组 ID
    if not group_id and group_username:
        from ..utils.bot_manager import bot_manager
        try:
            group_info = await bot_manager.resolve_group(group_username)
            if group_info:
                group_id = group_info['id']
                group_name = group_info.get('title')
            else:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="无法找到该群组，请确保机器人已加入该群组"
                )
        except HTTPException:
            raise
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"解析群组失败: {str(e)}"
            )
    
    # 检查是否已存在
    existing = await service.get_group_by_telegram_id(group_id)
    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="该群组已存在"
        )
    
    # 创建群组记录
    new_group = await service.create_group(
        group_id=group_id,
        group_name=group_name,
        group_username=group_username
    )
    
    # 通知 Bot 管理器添加群组监听
    from ..utils.bot_manager import bot_manager
    await bot_manager.add_group(group_id)
    
    return GroupResponse.model_validate(new_group)


@router.get("/{group_db_id}", response_model=GroupResponse)
async def get_group(
    group_db_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """获取单个群组详情"""
    service = DatabaseService(db)
    group = await service.get_group_by_id(group_db_id)
    
    if not group:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="群组不存在"
        )
    
    return GroupResponse.model_validate(group)


@router.put("/{group_db_id}", response_model=GroupResponse)
async def update_group(
    group_db_id: int,
    group_update: GroupUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """更新群组信息"""
    service = DatabaseService(db)
    
    group = await service.update_group(
        group_db_id,
        group_name=group_update.group_name,
        is_active=group_update.is_active
    )
    
    if not group:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="群组不存在"
        )
    
    # 如果状态变更，通知 Bot 管理器
    if group_update.is_active is not None:
        from ..utils.bot_manager import bot_manager
        if group_update.is_active:
            await bot_manager.add_group(group.group_id)
        else:
            await bot_manager.remove_group(group.group_id)
    
    return GroupResponse.model_validate(group)


@router.delete("/{group_db_id}", response_model=BaseResponse)
async def delete_group(
    group_db_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """删除群组"""
    service = DatabaseService(db)
    
    # 先获取群组信息
    group = await service.get_group_by_id(group_db_id)
    if not group:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="群组不存在"
        )
    
    # 从 Bot 管理器中移除
    from ..utils.bot_manager import bot_manager
    await bot_manager.remove_group(group.group_id)
    
    # 删除数据库记录
    success = await service.delete_group(group_db_id)
    
    if success:
        return BaseResponse(success=True, message="群组已删除")
    else:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="删除失败"
        )


@router.post("/{group_db_id}/refresh", response_model=GroupResponse)
async def refresh_group_info(
    group_db_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """刷新群组信息"""
    service = DatabaseService(db)
    group = await service.get_group_by_id(group_db_id)
    
    if not group:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="群组不存在"
        )
    
    # 通过 Bot 获取最新信息
    from ..utils.bot_manager import bot_manager
    try:
        group_info = await bot_manager.get_group_info(group.group_id)
        if group_info:
            group = await service.update_group(
                group_db_id,
                group_name=group_info.get('title')
            )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"刷新失败: {str(e)}"
        )
    
    return GroupResponse.model_validate(group)
