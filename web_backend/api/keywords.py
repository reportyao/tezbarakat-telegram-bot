"""
Tezbarakat Telegram Bot - 关键词管理 API
"""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Optional

import sys
sys.path.append('..')
from models.database import get_db
from models.schemas import (
    KeywordCreate, KeywordUpdate, KeywordResponse, KeywordListResponse,
    KeywordBatchCreate, BaseResponse
)
from services.db_service import DatabaseService
from services.auth_service import get_current_user

router = APIRouter(prefix="/keywords", tags=["关键词管理"])


@router.get("", response_model=KeywordListResponse)
async def get_keywords(
    active_only: bool = False,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """获取所有关键词列表"""
    service = DatabaseService(db)
    keywords = await service.get_all_keywords(active_only=active_only)
    
    return KeywordListResponse(
        total=len(keywords),
        keywords=[KeywordResponse.model_validate(k) for k in keywords]
    )


@router.post("", response_model=KeywordResponse)
async def create_keyword(
    keyword: KeywordCreate,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """添加新关键词"""
    service = DatabaseService(db)
    
    # 检查是否已存在
    existing_keywords = await service.get_all_keywords()
    keyword_text = keyword.keyword.lower().strip()
    
    for k in existing_keywords:
        if k.keyword == keyword_text:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="该关键词已存在"
            )
    
    new_keyword = await service.create_keyword(keyword_text)
    
    # 通知 Bot 管理器更新关键词列表
    from utils.bot_manager import bot_manager
    await bot_manager.reload_keywords()
    
    return KeywordResponse.model_validate(new_keyword)


@router.post("/batch", response_model=BaseResponse)
async def create_keywords_batch(
    batch: KeywordBatchCreate,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """批量添加关键词"""
    service = DatabaseService(db)
    
    created = await service.create_keywords_batch(batch.keywords)
    
    # 通知 Bot 管理器更新关键词列表
    from utils.bot_manager import bot_manager
    await bot_manager.reload_keywords()
    
    return BaseResponse(
        success=True,
        message=f"成功添加 {len(created)} 个关键词"
    )


@router.get("/{keyword_id}", response_model=KeywordResponse)
async def get_keyword(
    keyword_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """获取单个关键词详情"""
    service = DatabaseService(db)
    keyword = await service.get_keyword_by_id(keyword_id)
    
    if not keyword:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="关键词不存在"
        )
    
    return KeywordResponse.model_validate(keyword)


@router.put("/{keyword_id}", response_model=KeywordResponse)
async def update_keyword(
    keyword_id: int,
    keyword_update: KeywordUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """更新关键词"""
    service = DatabaseService(db)
    
    keyword = await service.update_keyword(
        keyword_id,
        keyword=keyword_update.keyword,
        is_active=keyword_update.is_active
    )
    
    if not keyword:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="关键词不存在"
        )
    
    # 通知 Bot 管理器更新关键词列表
    from utils.bot_manager import bot_manager
    await bot_manager.reload_keywords()
    
    return KeywordResponse.model_validate(keyword)


@router.delete("/{keyword_id}", response_model=BaseResponse)
async def delete_keyword(
    keyword_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """删除关键词"""
    service = DatabaseService(db)
    
    success = await service.delete_keyword(keyword_id)
    
    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="关键词不存在"
        )
    
    # 通知 Bot 管理器更新关键词列表
    from utils.bot_manager import bot_manager
    await bot_manager.reload_keywords()
    
    return BaseResponse(success=True, message="关键词已删除")


@router.get("/stats/top", response_model=KeywordListResponse)
async def get_top_keywords(
    limit: int = 10,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """获取命中次数最多的关键词"""
    service = DatabaseService(db)
    keywords = await service.get_all_keywords()
    
    # 按命中次数排序
    sorted_keywords = sorted(keywords, key=lambda k: k.hit_count, reverse=True)[:limit]
    
    return KeywordListResponse(
        total=len(sorted_keywords),
        keywords=[KeywordResponse.model_validate(k) for k in sorted_keywords]
    )
