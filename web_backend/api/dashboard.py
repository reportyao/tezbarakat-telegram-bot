"""
Tezbarakat Telegram Bot - 仪表盘 API
"""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List
from datetime import date, timedelta

import sys
sys.path.append('..')
from models.database import get_db
from models.schemas import (
    DashboardData, DashboardStats, StatisticResponse, StatisticsListResponse, ChartData,
    BotStatus, TodayStats, AccountStatusSummary, RecentStatItem, AlertResponse
)
from services.db_service import DatabaseService
from services.auth_service import get_current_user

router = APIRouter(prefix="/dashboard", tags=["仪表盘"])


@router.get("", response_model=DashboardData)
async def get_dashboard(
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """获取仪表盘统计数据 - 返回前端期望的数据结构"""
    service = DatabaseService(db)
    stats = await service.get_dashboard_stats()
    
    # 获取 Bot 运行状态
    from ..utils.bot_manager import bot_manager
    bot_running = bot_manager.is_running()
    bot_uptime = bot_manager.get_uptime()
    connected_accounts = bot_manager.get_connected_accounts()
    monitored_groups = bot_manager.get_monitored_groups()
    
    # 构建 Bot 状态
    bot_status = BotStatus(
        running=bot_running,
        uptime=bot_uptime,
        connected_accounts=connected_accounts,
        monitored_groups=monitored_groups
    )
    
    # 构建今日统计
    today_stats = TodayStats(
        total_messages_monitored=stats['today_messages'],
        keyword_triggered_count=stats['today_keyword_triggers'],
        dify_triggered_count=stats['today_dify_triggers'],
        group_replies_sent=stats['today_group_replies'],
        private_messages_sent=stats['today_private_messages'],
        new_users_count=stats['today_new_users']
    )
    
    # 构建账号状态汇总
    account_status = AccountStatusSummary(
        total=stats['total_accounts'],
        active=stats['active_accounts'],
        cooling_down=stats.get('cooling_down_accounts', 0),
        limited=stats['limited_accounts'],
        banned=stats['banned_accounts']
    )
    
    # 获取近7天统计
    statistics = await service.get_statistics(7)
    recent_stats = []
    start_date = date.today() - timedelta(days=6)
    stats_dict = {s.date: s for s in statistics}
    
    for i in range(7):
        current_date = start_date + timedelta(days=i)
        if current_date in stats_dict:
            s = stats_dict[current_date]
            recent_stats.append(RecentStatItem(
                date=current_date.strftime("%m/%d"),
                total_messages_monitored=s.total_messages_monitored,
                keyword_triggered_count=s.keyword_triggered_count,
                dify_triggered_count=s.dify_triggered_count,
                group_replies_sent=s.group_replies_sent,
                private_messages_sent=s.private_messages_sent
            ))
        else:
            recent_stats.append(RecentStatItem(
                date=current_date.strftime("%m/%d"),
                total_messages_monitored=0,
                keyword_triggered_count=0,
                dify_triggered_count=0,
                group_replies_sent=0,
                private_messages_sent=0
            ))
    
    # 获取最近告警
    alerts, _, _ = await service.get_alerts(page=1, page_size=5, unread_only=False)
    recent_alerts = [AlertResponse.model_validate(a) for a in alerts]
    
    return DashboardData(
        bot_status=bot_status,
        today_stats=today_stats,
        recent_stats=recent_stats,
        account_status=account_status,
        recent_alerts=recent_alerts
    )


@router.get("/stats", response_model=DashboardStats)
async def get_dashboard_stats(
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """获取仪表盘统计数据（旧版 API，保留兼容）"""
    service = DatabaseService(db)
    stats = await service.get_dashboard_stats()
    
    # 获取 Bot 运行状态
    from ..utils.bot_manager import bot_manager
    bot_running = bot_manager.is_running()
    
    return DashboardStats(
        today_messages=stats['today_messages'],
        today_keyword_triggers=stats['today_keyword_triggers'],
        today_dify_triggers=stats['today_dify_triggers'],
        today_group_replies=stats['today_group_replies'],
        today_private_messages=stats['today_private_messages'],
        today_new_users=stats['today_new_users'],
        total_accounts=stats['total_accounts'],
        active_accounts=stats['active_accounts'],
        limited_accounts=stats['limited_accounts'],
        banned_accounts=stats['banned_accounts'],
        total_groups=stats['total_groups'],
        active_groups=stats['active_groups'],
        total_keywords=stats['total_keywords'],
        active_keywords=stats['active_keywords'],
        unread_alerts=stats['unread_alerts'],
        bot_running=bot_running
    )


@router.get("/statistics", response_model=StatisticsListResponse)
async def get_statistics(
    days: int = 7,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """获取历史统计数据"""
    if days < 1 or days > 90:
        raise HTTPException(status_code=400, detail="天数必须在 1-90 之间")
    
    service = DatabaseService(db)
    statistics = await service.get_statistics(days)
    
    return StatisticsListResponse(
        statistics=[StatisticResponse.model_validate(s) for s in statistics]
    )


@router.get("/chart/messages", response_model=ChartData)
async def get_messages_chart(
    days: int = 7,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """获取消息统计图表数据"""
    service = DatabaseService(db)
    statistics = await service.get_statistics(days)
    
    # 构建日期标签
    labels = []
    messages_data = []
    keyword_data = []
    dify_data = []
    
    start_date = date.today() - timedelta(days=days - 1)
    stats_dict = {s.date: s for s in statistics}
    
    for i in range(days):
        current_date = start_date + timedelta(days=i)
        labels.append(current_date.strftime("%m/%d"))
        
        if current_date in stats_dict:
            s = stats_dict[current_date]
            messages_data.append(s.total_messages_monitored)
            keyword_data.append(s.keyword_triggered_count)
            dify_data.append(s.dify_triggered_count)
        else:
            messages_data.append(0)
            keyword_data.append(0)
            dify_data.append(0)
    
    return ChartData(
        labels=labels,
        datasets=[
            {
                "label": "监听消息",
                "data": messages_data,
                "borderColor": "#3B82F6",
                "backgroundColor": "rgba(59, 130, 246, 0.1)"
            },
            {
                "label": "关键词触发",
                "data": keyword_data,
                "borderColor": "#10B981",
                "backgroundColor": "rgba(16, 185, 129, 0.1)"
            },
            {
                "label": "Dify 触发",
                "data": dify_data,
                "borderColor": "#F59E0B",
                "backgroundColor": "rgba(245, 158, 11, 0.1)"
            }
        ]
    )


@router.get("/chart/replies", response_model=ChartData)
async def get_replies_chart(
    days: int = 7,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """获取回复统计图表数据"""
    service = DatabaseService(db)
    statistics = await service.get_statistics(days)
    
    labels = []
    group_data = []
    private_data = []
    
    start_date = date.today() - timedelta(days=days - 1)
    stats_dict = {s.date: s for s in statistics}
    
    for i in range(days):
        current_date = start_date + timedelta(days=i)
        labels.append(current_date.strftime("%m/%d"))
        
        if current_date in stats_dict:
            s = stats_dict[current_date]
            group_data.append(s.group_replies_sent)
            private_data.append(s.private_messages_sent)
        else:
            group_data.append(0)
            private_data.append(0)
    
    return ChartData(
        labels=labels,
        datasets=[
            {
                "label": "群内回复",
                "data": group_data,
                "borderColor": "#8B5CF6",
                "backgroundColor": "rgba(139, 92, 246, 0.1)"
            },
            {
                "label": "私信发送",
                "data": private_data,
                "borderColor": "#EC4899",
                "backgroundColor": "rgba(236, 72, 153, 0.1)"
            }
        ]
    )
