"""
Tezbarakat Telegram Bot - 消息和回复记录 API
"""

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Optional

import sys
sys.path.append('..')
from models.database import get_db
from models.schemas import (
    MessageResponse, MessageListResponse,
    ReplyResponse, ReplyListResponse,
    UserResponse, UserListResponse,
    ConversationResponse, ConversationListResponse,
    PaginatedResponse
)
from services.db_service import DatabaseService
from services.auth_service import get_current_user

router = APIRouter(tags=["消息记录"])


# =====================================================
# 消息记录
# =====================================================

@router.get("/messages", response_model=MessageListResponse)
async def get_messages(
    page: int = Query(1, ge=1),
    page_size: int = Query(50, ge=1, le=100),
    group_id: Optional[int] = None,
    user_id: Optional[int] = None,
    triggered_only: bool = False,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """获取消息记录列表"""
    service = DatabaseService(db)
    messages, total = await service.get_messages(
        page=page,
        page_size=page_size,
        group_id=group_id,
        user_id=user_id,
        triggered_only=triggered_only
    )
    
    return MessageListResponse(
        total=total,
        messages=[MessageResponse.model_validate(m) for m in messages]
    )


# =====================================================
# 回复记录
# =====================================================

@router.get("/replies", response_model=ReplyListResponse)
async def get_replies(
    page: int = Query(1, ge=1),
    page_size: int = Query(50, ge=1, le=100),
    reply_type: Optional[str] = Query(None, pattern="^(group|private)$"),
    account_id: Optional[int] = None,
    user_id: Optional[int] = None,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """获取回复记录列表"""
    service = DatabaseService(db)
    replies, total = await service.get_replies(
        page=page,
        page_size=page_size,
        reply_type=reply_type,
        account_id=account_id,
        user_id=user_id
    )
    
    return ReplyListResponse(
        total=total,
        replies=[ReplyResponse.model_validate(r) for r in replies]
    )


# =====================================================
# 用户记录
# =====================================================

@router.get("/users", response_model=UserListResponse)
async def get_users(
    page: int = Query(1, ge=1),
    page_size: int = Query(50, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """获取用户列表"""
    service = DatabaseService(db)
    users, total = await service.get_all_users(page=page, page_size=page_size)
    
    return UserListResponse(
        total=total,
        users=[UserResponse.model_validate(u) for u in users]
    )


@router.get("/users/{user_id}", response_model=UserResponse)
async def get_user(
    user_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """获取单个用户详情"""
    service = DatabaseService(db)
    user = await service.get_user(user_id)
    
    if not user:
        raise HTTPException(
            status_code=404,
            detail="用户不存在"
        )
    
    return UserResponse.model_validate(user)


@router.get("/users/{user_id}/messages", response_model=MessageListResponse)
async def get_user_messages(
    user_id: int,
    page: int = Query(1, ge=1),
    page_size: int = Query(50, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """获取用户的消息记录"""
    service = DatabaseService(db)
    messages, total = await service.get_messages(
        page=page,
        page_size=page_size,
        user_id=user_id
    )
    
    return MessageListResponse(
        total=total,
        messages=[MessageResponse.model_validate(m) for m in messages]
    )


@router.get("/users/{user_id}/replies", response_model=ReplyListResponse)
async def get_user_replies(
    user_id: int,
    page: int = Query(1, ge=1),
    page_size: int = Query(50, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """获取发送给用户的回复记录"""
    service = DatabaseService(db)
    replies, total = await service.get_replies(
        page=page,
        page_size=page_size,
        user_id=user_id
    )
    
    return ReplyListResponse(
        total=total,
        replies=[ReplyResponse.model_validate(r) for r in replies]
    )
