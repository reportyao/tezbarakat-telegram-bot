"""
Tezbarakat Telegram Bot - Pydantic 数据模型
用于 API 请求/响应的数据验证和序列化
"""

from datetime import datetime, date
from typing import Optional, List, Any, Dict
from pydantic import BaseModel, Field, ConfigDict


# =====================================================
# 基础模型
# =====================================================

class BaseResponse(BaseModel):
    """基础响应模型"""
    success: bool = True
    message: str = "操作成功"


class PaginatedResponse(BaseModel):
    """分页响应模型"""
    total: int
    page: int
    page_size: int
    total_pages: int
    items: List[Any]


# =====================================================
# 账号相关模型
# =====================================================

class AccountBase(BaseModel):
    """账号基础模型"""
    phone_number: str = Field(..., min_length=5, max_length=20, description="手机号")


class AccountCreate(AccountBase):
    """创建账号请求"""
    session_name: Optional[str] = Field(None, max_length=50, description="Session 名称")


class AccountLogin(BaseModel):
    """账号登录请求"""
    phone_number: str = Field(..., description="手机号")
    code: Optional[str] = Field(None, description="验证码")
    password: Optional[str] = Field(None, description="两步验证密码")


class AccountResponse(AccountBase):
    """账号响应模型"""
    model_config = ConfigDict(from_attributes=True)
    
    id: int
    session_name: str
    status: str
    last_used_at: Optional[datetime] = None
    daily_message_count: int = 0
    created_at: datetime
    updated_at: datetime


class AccountStatusUpdate(BaseModel):
    """账号状态更新请求"""
    status: str = Field(..., pattern="^(active|cooling_down|limited|banned)$")


class AccountListResponse(BaseModel):
    """账号列表响应"""
    total: int
    accounts: List[AccountResponse]


# =====================================================
# 群组相关模型
# =====================================================

class GroupBase(BaseModel):
    """群组基础模型"""
    group_id: int = Field(..., description="Telegram 群组 ID")
    group_name: Optional[str] = Field(None, max_length=255, description="群组名称")
    group_username: Optional[str] = Field(None, max_length=255, description="群组用户名")


class GroupCreate(BaseModel):
    """创建群组请求"""
    group_id: Optional[int] = Field(None, description="Telegram 群组 ID")
    group_name: Optional[str] = Field(None, description="群组名称")
    group_username: Optional[str] = Field(None, description="群组用户名或链接")


class GroupUpdate(BaseModel):
    """更新群组请求"""
    group_name: Optional[str] = None
    is_active: Optional[bool] = None


class GroupResponse(GroupBase):
    """群组响应模型"""
    model_config = ConfigDict(from_attributes=True)
    
    id: int
    is_active: bool
    hourly_reply_count: int = 0
    created_at: datetime


class GroupListResponse(BaseModel):
    """群组列表响应"""
    total: int
    groups: List[GroupResponse]


# =====================================================
# 关键词相关模型
# =====================================================

class KeywordBase(BaseModel):
    """关键词基础模型"""
    keyword: str = Field(..., min_length=1, max_length=100, description="关键词")


class KeywordCreate(KeywordBase):
    """创建关键词请求"""
    pass


class KeywordUpdate(BaseModel):
    """更新关键词请求"""
    keyword: Optional[str] = Field(None, min_length=1, max_length=100)
    is_active: Optional[bool] = None


class KeywordResponse(KeywordBase):
    """关键词响应模型"""
    model_config = ConfigDict(from_attributes=True)
    
    id: int
    is_active: bool
    hit_count: int = 0
    created_at: datetime


class KeywordListResponse(BaseModel):
    """关键词列表响应"""
    total: int
    keywords: List[KeywordResponse]


class KeywordBatchCreate(BaseModel):
    """批量创建关键词请求"""
    keywords: List[str] = Field(..., min_length=1, description="关键词列表")


# =====================================================
# 用户相关模型
# =====================================================

class UserResponse(BaseModel):
    """用户响应模型"""
    model_config = ConfigDict(from_attributes=True)
    
    user_id: int
    username: Optional[str] = None
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    last_private_message_time: Optional[datetime] = None
    total_messages_received: int = 0
    created_at: datetime


class UserListResponse(BaseModel):
    """用户列表响应"""
    total: int
    users: List[UserResponse]


# =====================================================
# 消息相关模型
# =====================================================

class MessageResponse(BaseModel):
    """消息响应模型"""
    model_config = ConfigDict(from_attributes=True)
    
    id: int
    timestamp: datetime
    group_id: int
    user_id: int
    message_id: Optional[int] = None
    text: Optional[str] = None
    triggered_keyword: bool = False
    matched_keyword: Optional[str] = None
    triggered_dify: bool = False
    dify_confidence: Optional[float] = None
    created_at: datetime


class MessageListResponse(BaseModel):
    """消息列表响应"""
    total: int
    messages: List[MessageResponse]


# =====================================================
# 回复相关模型
# =====================================================

class ReplyResponse(BaseModel):
    """回复响应模型"""
    model_config = ConfigDict(from_attributes=True)
    
    id: int
    timestamp: datetime
    account_id: Optional[int] = None
    user_id: int
    group_id: Optional[int] = None
    type: str
    sent_text: Optional[str] = None
    conversation_id: Optional[str] = None
    status: str = "sent"
    error_message: Optional[str] = None
    created_at: datetime


class ReplyListResponse(BaseModel):
    """回复列表响应"""
    total: int
    replies: List[ReplyResponse]


# =====================================================
# 对话相关模型
# =====================================================

class ConversationResponse(BaseModel):
    """对话响应模型"""
    model_config = ConfigDict(from_attributes=True)
    
    id: int
    user_id: int
    account_id: Optional[int] = None
    dify_conversation_id: Optional[str] = None
    status: str
    message_count: int = 0
    last_message_at: datetime
    created_at: datetime


class ConversationListResponse(BaseModel):
    """对话列表响应"""
    total: int
    conversations: List[ConversationResponse]


# =====================================================
# 配置相关模型
# =====================================================

class ConfigItem(BaseModel):
    """配置项模型"""
    key: str
    value: Any
    description: Optional[str] = None


class ConfigUpdate(BaseModel):
    """配置更新请求"""
    value: Any


class ConfigResponse(BaseModel):
    """配置响应模型"""
    model_config = ConfigDict(from_attributes=True)
    
    key: str
    value: Any
    description: Optional[str] = None
    updated_at: datetime


class ConfigListResponse(BaseModel):
    """配置列表响应"""
    configs: List[ConfigResponse]


class ConfigBatchUpdate(BaseModel):
    """批量配置更新请求"""
    configs: Dict[str, Any]


# =====================================================
# 告警相关模型
# =====================================================

class AlertResponse(BaseModel):
    """告警响应模型"""
    model_config = ConfigDict(from_attributes=True)
    
    id: int
    type: str
    severity: str
    title: str
    message: Optional[str] = None
    account_id: Optional[int] = None
    is_read: bool = False
    created_at: datetime


class AlertListResponse(BaseModel):
    """告警列表响应"""
    total: int
    unread_count: int
    alerts: List[AlertResponse]


class AlertMarkRead(BaseModel):
    """标记告警已读请求"""
    alert_ids: List[int] = Field(..., min_length=1)


# =====================================================
# 统计相关模型
# =====================================================

class TodayStats(BaseModel):
    """今日统计数据"""
    total_messages_monitored: int = 0
    keyword_triggered_count: int = 0
    dify_triggered_count: int = 0
    group_replies_sent: int = 0
    private_messages_sent: int = 0
    new_users_count: int = 0


class AccountStatusSummary(BaseModel):
    """账号状态汇总"""
    total: int = 0
    active: int = 0
    cooling_down: int = 0
    limited: int = 0
    banned: int = 0


class RecentStatItem(BaseModel):
    """近期统计项"""
    date: str
    total_messages_monitored: int = 0
    keyword_triggered_count: int = 0
    dify_triggered_count: int = 0
    group_replies_sent: int = 0
    private_messages_sent: int = 0


class DashboardData(BaseModel):
    """仪表盘完整数据 - 匹配前端期望的数据结构"""
    bot_status: 'BotStatus'
    today_stats: TodayStats
    recent_stats: List[RecentStatItem]
    account_status: AccountStatusSummary
    recent_alerts: List[AlertResponse]


class DashboardStats(BaseModel):
    """仪表盘统计数据（旧版，保留兼容）"""
    # 今日统计
    today_messages: int = 0
    today_keyword_triggers: int = 0
    today_dify_triggers: int = 0
    today_group_replies: int = 0
    today_private_messages: int = 0
    today_new_users: int = 0
    
    # 账号统计
    total_accounts: int = 0
    active_accounts: int = 0
    limited_accounts: int = 0
    banned_accounts: int = 0
    
    # 群组统计
    total_groups: int = 0
    active_groups: int = 0
    
    # 关键词统计
    total_keywords: int = 0
    active_keywords: int = 0
    
    # 告警统计
    unread_alerts: int = 0
    
    # 系统状态
    bot_running: bool = False


class StatisticResponse(BaseModel):
    """统计响应模型"""
    model_config = ConfigDict(from_attributes=True)
    
    id: int
    date: date
    total_messages_monitored: int = 0
    keyword_triggered_count: int = 0
    dify_triggered_count: int = 0
    group_replies_sent: int = 0
    private_messages_sent: int = 0
    new_users_count: int = 0
    active_accounts_count: int = 0


class StatisticsListResponse(BaseModel):
    """统计列表响应"""
    statistics: List[StatisticResponse]


class ChartData(BaseModel):
    """图表数据"""
    labels: List[str]
    datasets: List[Dict[str, Any]]


# =====================================================
# 认证相关模型
# =====================================================

class LoginRequest(BaseModel):
    """登录请求"""
    username: str
    password: str


class TokenResponse(BaseModel):
    """Token 响应"""
    access_token: str
    token_type: str = "bearer"
    expires_in: int


# =====================================================
# Bot 控制相关模型
# =====================================================

class BotStatus(BaseModel):
    """Bot 状态"""
    running: bool
    uptime: Optional[int] = None  # 运行时间（秒）
    connected_accounts: int = 0
    monitored_groups: int = 0
    last_message_time: Optional[datetime] = None


class BotControlRequest(BaseModel):
    """Bot 控制请求"""
    action: str = Field(..., pattern="^(start|stop|restart)$")


# =====================================================
# WebSocket 消息模型
# =====================================================

class WSMessage(BaseModel):
    """WebSocket 消息"""
    type: str  # log, alert, status, message
    data: Any
    timestamp: datetime = Field(default_factory=datetime.now)


class LogEntry(BaseModel):
    """日志条目"""
    level: str
    message: str
    module: Optional[str] = None
    timestamp: datetime = Field(default_factory=datetime.now)


# 更新前向引用
DashboardData.model_rebuild()
