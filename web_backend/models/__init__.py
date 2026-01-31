"""
Tezbarakat Telegram Bot - 数据模型包
"""

from .database import (
    Base,
    engine,
    async_session_maker,
    get_db,
    init_db,
    Account,
    Group,
    Keyword,
    User,
    Message,
    Reply,
    Conversation,
    AppConfig,
    Alert,
    Statistic
)

from .schemas import (
    # 基础模型
    BaseResponse,
    PaginatedResponse,
    
    # 账号模型
    AccountBase,
    AccountCreate,
    AccountLogin,
    AccountResponse,
    AccountStatusUpdate,
    AccountListResponse,
    
    # 群组模型
    GroupBase,
    GroupCreate,
    GroupUpdate,
    GroupResponse,
    GroupListResponse,
    
    # 关键词模型
    KeywordBase,
    KeywordCreate,
    KeywordUpdate,
    KeywordResponse,
    KeywordListResponse,
    KeywordBatchCreate,
    
    # 用户模型
    UserResponse,
    UserListResponse,
    
    # 消息模型
    MessageResponse,
    MessageListResponse,
    
    # 回复模型
    ReplyResponse,
    ReplyListResponse,
    
    # 对话模型
    ConversationResponse,
    ConversationListResponse,
    
    # 配置模型
    ConfigItem,
    ConfigUpdate,
    ConfigResponse,
    ConfigListResponse,
    ConfigBatchUpdate,
    
    # 告警模型
    AlertResponse,
    AlertListResponse,
    AlertMarkRead,
    
    # 统计模型
    DashboardStats,
    StatisticResponse,
    StatisticsListResponse,
    ChartData,
    
    # 认证模型
    LoginRequest,
    TokenResponse,
    
    # Bot 控制模型
    BotStatus,
    BotControlRequest,
    
    # WebSocket 模型
    WSMessage,
    LogEntry
)

__all__ = [
    # Database
    'Base', 'engine', 'async_session_maker', 'get_db', 'init_db',
    'Account', 'Group', 'Keyword', 'User', 'Message', 'Reply',
    'Conversation', 'AppConfig', 'Alert', 'Statistic',
    
    # Schemas
    'BaseResponse', 'PaginatedResponse',
    'AccountBase', 'AccountCreate', 'AccountLogin', 'AccountResponse',
    'AccountStatusUpdate', 'AccountListResponse',
    'GroupBase', 'GroupCreate', 'GroupUpdate', 'GroupResponse', 'GroupListResponse',
    'KeywordBase', 'KeywordCreate', 'KeywordUpdate', 'KeywordResponse',
    'KeywordListResponse', 'KeywordBatchCreate',
    'UserResponse', 'UserListResponse',
    'MessageResponse', 'MessageListResponse',
    'ReplyResponse', 'ReplyListResponse',
    'ConversationResponse', 'ConversationListResponse',
    'ConfigItem', 'ConfigUpdate', 'ConfigResponse', 'ConfigListResponse', 'ConfigBatchUpdate',
    'AlertResponse', 'AlertListResponse', 'AlertMarkRead',
    'DashboardStats', 'StatisticResponse', 'StatisticsListResponse', 'ChartData',
    'LoginRequest', 'TokenResponse',
    'BotStatus', 'BotControlRequest',
    'WSMessage', 'LogEntry'
]
