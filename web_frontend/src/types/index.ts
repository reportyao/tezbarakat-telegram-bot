// API 响应类型
export interface BaseResponse {
  success: boolean;
  message?: string;
}

// 账号类型
export interface Account {
  id: number;
  phone_number: string;
  session_name: string;
  status: 'active' | 'limited' | 'banned' | 'logging_in' | 'need_password';
  last_used_at?: string;
  daily_message_count: number;
  created_at: string;
  updated_at: string;
}

// 群组类型
export interface Group {
  id: number;
  group_id: number;
  group_name: string;
  group_username?: string;
  is_active: boolean;
  member_count?: number;
  hourly_reply_count: number;
  created_at: string;
}

// 关键词类型
export interface Keyword {
  id: number;
  keyword: string;
  is_active: boolean;
  hit_count: number;
  created_at: string;
}

// 用户类型
export interface User {
  user_id: number;
  username?: string;
  first_name?: string;
  last_name?: string;
  last_private_message_time?: string;
  total_messages_received: number;
  created_at: string;
}

// 消息类型
export interface Message {
  id: number;
  timestamp: string;
  group_id: number;
  user_id: number;
  message_id?: number;
  text: string;
  triggered_keyword: boolean;
  matched_keyword?: string;
  triggered_dify: boolean;
  dify_confidence?: number;
}

// 回复类型
export interface Reply {
  id: number;
  timestamp: string;
  account_id?: number;
  user_id: number;
  group_id?: number;
  type: 'group' | 'private';
  sent_text?: string;
  conversation_id?: string;
  status: 'sent' | 'failed';
  error_message?: string;
}

// 配置类型
export interface Config {
  key: string;
  value: any;
  description?: string;
}

// 告警类型
export interface Alert {
  id: number;
  type: string;
  title: string;
  message?: string;
  severity: 'info' | 'warning' | 'error';
  is_read: boolean;
  account_id?: number;
  created_at: string;
}

// 统计类型
export interface Statistic {
  date: string;
  total_messages_monitored: number;
  keyword_triggered_count: number;
  dify_triggered_count: number;
  group_replies_sent: number;
  private_messages_sent: number;
  new_users_count: number;
  active_conversations: number;
}

// 仪表盘数据类型
export interface DashboardData {
  bot_status: {
    running: boolean;
    uptime?: number;
    connected_accounts: number;
    monitored_groups: number;
    last_message_time?: string;
  };
  today_stats: Statistic;
  recent_stats: Statistic[];
  account_status: {
    total: number;
    active: number;
    limited: number;
    banned: number;
  };
  recent_alerts: Alert[];
}

// Bot 状态类型
export interface BotStatus {
  running: boolean;
  uptime?: number;
  connected_accounts: number;
  monitored_groups: number;
  last_message_time?: string;
}

// 登录请求类型
export interface LoginRequest {
  username: string;
  password: string;
}

// Token 响应类型
export interface TokenResponse {
  access_token: string;
  token_type: string;
  expires_in: number;
}

// 分页响应类型
export interface PaginatedResponse<T> {
  total: number;
  items: T[];
}

// WebSocket 消息类型
export interface WSMessage {
  type: 'log' | 'alert' | 'status' | 'message' | 'connected';
  data: any;
}

// 日志条目类型
export interface LogEntry {
  level: string;
  message: string;
  module?: string;
  timestamp: string;
}
