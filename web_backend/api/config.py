"""
Tezbarakat Telegram Bot - 配置和告警 API
"""

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Optional

import sys
sys.path.append('..')
from models.database import get_db
from models.schemas import (
    ConfigResponse, ConfigListResponse, ConfigUpdate, ConfigBatchUpdate,
    AlertResponse, AlertListResponse, AlertMarkRead,
    BaseResponse
)
from services.db_service import DatabaseService
from services.auth_service import get_current_user

router = APIRouter(tags=["配置管理"])


# =====================================================
# 配置管理
# =====================================================

@router.get("/config", response_model=ConfigListResponse)
async def get_all_configs(
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """获取所有配置项"""
    service = DatabaseService(db)
    configs = await service.get_all_configs()
    
    return ConfigListResponse(
        configs=[ConfigResponse.model_validate(c) for c in configs]
    )


@router.get("/config/{key}", response_model=ConfigResponse)
async def get_config(
    key: str,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """获取单个配置项"""
    service = DatabaseService(db)
    configs = await service.get_all_configs()
    
    for c in configs:
        if c.key == key:
            return ConfigResponse.model_validate(c)
    
    raise HTTPException(
        status_code=404,
        detail="配置项不存在"
    )


@router.put("/config/{key}", response_model=ConfigResponse)
async def update_config(
    key: str,
    config_update: ConfigUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """更新配置项"""
    service = DatabaseService(db)
    config = await service.set_config(key, config_update.value)
    
    # 通知 Bot 管理器重新加载配置
    from utils.bot_manager import bot_manager
    await bot_manager.reload_config()
    
    return ConfigResponse.model_validate(config)


@router.put("/config", response_model=BaseResponse)
async def update_configs_batch(
    batch: ConfigBatchUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """批量更新配置项"""
    service = DatabaseService(db)
    await service.set_configs_batch(batch.configs)
    
    # 通知 Bot 管理器重新加载配置
    from utils.bot_manager import bot_manager
    await bot_manager.reload_config()
    
    return BaseResponse(
        success=True,
        message=f"成功更新 {len(batch.configs)} 个配置项"
    )


# =====================================================
# 告警管理
# =====================================================

@router.get("/alerts", response_model=AlertListResponse)
async def get_alerts(
    page: int = Query(1, ge=1),
    page_size: int = Query(50, ge=1, le=100),
    unread_only: bool = False,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """获取告警列表"""
    service = DatabaseService(db)
    alerts, total, unread_count = await service.get_alerts(
        page=page,
        page_size=page_size,
        unread_only=unread_only
    )
    
    return AlertListResponse(
        total=total,
        unread_count=unread_count,
        alerts=[AlertResponse.model_validate(a) for a in alerts]
    )


@router.post("/alerts/read", response_model=BaseResponse)
async def mark_alerts_read(
    mark_read: AlertMarkRead,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """标记告警已读"""
    service = DatabaseService(db)
    await service.mark_alerts_read(mark_read.alert_ids)
    
    return BaseResponse(
        success=True,
        message=f"已标记 {len(mark_read.alert_ids)} 条告警为已读"
    )


@router.post("/alerts/read-all", response_model=BaseResponse)
async def mark_all_alerts_read(
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """标记所有告警已读"""
    service = DatabaseService(db)
    await service.mark_all_alerts_read()
    
    return BaseResponse(
        success=True,
        message="已标记所有告警为已读"
    )
