# Tezbarakat Telegram Bot - 功能需求检查清单

## 1. 核心功能需求

### 1.1 多群组实时监控
- [ ] 同时监控多达100个群组
- [ ] 使用主监听账号接入所有目标群组

### 1.2 智能意图识别
- [ ] 关键词触发（支持塔吉克语、俄语，不区分大小写）
- [ ] Dify AI 工作流意图分析
- [ ] 置信度阈值判断

### 1.3 双层回复策略
- [ ] 群内@用户进行简短互动（引用原消息）
- [ ] 私信发送详细平台介绍
- [ ] 一次 Dify 调用生成两种回复文本

### 1.4 多账号防风控
- [ ] 最多20个小号轮换
- [ ] 账号状态机管理 (logging_in, active, cooling_down, limited, banned)
- [ ] 优先选择 last_used_at 最早的账号

### 1.5 持续对话能力
- [ ] 监听用户私信回复
- [ ] 调用 Dify 知识库进行多轮对话
- [ ] 使用 conversation_id 追踪上下文

### 1.6 可视化 Web 管理后台
- [ ] 仪表盘（核心指标、账号状态图、告警、实时日志）
- [ ] 账号管理（列表、添加、登录流程）
- [ ] 群组管理（增删改查、启用/禁用）
- [ ] 关键词管理（增删改查、启用/禁用）
- [ ] 系统配置（动态修改配置项）
- [ ] 消息记录查询

### 1.7 动态配置管理
- [ ] 无需重启服务即可添加/移除群组
- [ ] 无需重启服务即可添加/移除关键词

### 1.8 异常告警
- [ ] 账号封禁告警
- [ ] API 失败告警
- [ ] WebSocket 实时推送告警

## 2. 防风控策略

### 2.1 频率控制
- [ ] 单账号私信间隔 ≥ 5 分钟
- [ ] 单账号每日私信上限 20 条
- [ ] 单群每小时回复上限 3 条
- [ ] 用户冷却期 3 天

### 2.2 真人模拟行为
- [ ] 打字状态模拟（2-5秒随机）
- [ ] 发送延迟随机化（10-60秒）
- [ ] 活跃时段控制（早8点至晚12点，塔吉克斯坦时间）

### 2.3 账号状态自动检测
- [ ] FloodWaitError 处理（设为 limited，等待后恢复）
- [ ] UserBannedInChannelError / ChatWriteForbiddenError 处理
- [ ] AuthKeyUnregisteredError 处理（设为 banned，发出告警）
- [ ] 心跳检测（定期检测账号有效性）

## 3. API 端点需求

### 3.1 后端 API
- [ ] GET /api/dashboard - 聚合统计数据
- [ ] GET /api/accounts - 获取所有账号
- [ ] POST /api/accounts - 创建新账号（触发登录流程）
- [ ] POST /api/accounts/login - 完成登录（验证码/密码）
- [ ] GET/POST/PUT/DELETE /api/groups - 群组管理
- [ ] GET/POST/PUT/DELETE /api/keywords - 关键词管理
- [ ] GET /api/messages - 消息记录查询
- [ ] GET /api/config - 获取配置
- [ ] PUT /api/config - 更新配置
- [ ] WebSocket /ws/logs - 实时日志推送
- [ ] WebSocket /ws/alerts - 实时告警推送

## 4. 数据库表需求

### 4.1 accounts 表
- [ ] id, phone_number, session_name, status, last_used_at, created_at, updated_at
- [ ] daily_message_count, daily_reset_date（每日私信计数）

### 4.2 groups 表
- [ ] id, group_id, group_name, is_active, created_at
- [ ] hourly_reply_count, hourly_reset_time（每小时回复计数）

### 4.3 keywords 表
- [ ] id, keyword, is_active, created_at
- [ ] hit_count（命中计数）

### 4.4 messages 表
- [ ] id, timestamp, group_id, user_id, text, triggered_keyword, triggered_dify
- [ ] message_id, matched_keyword, dify_confidence

### 4.5 replies 表
- [ ] id, timestamp, account_id, user_id, group_id, type, sent_text, conversation_id
- [ ] status, error_message

### 4.6 users 表
- [ ] user_id, username, last_private_message_time, created_at
- [ ] first_name, last_name, total_messages_received

### 4.7 app_config 表
- [ ] key, value (JSONB), description

### 4.8 conversations 表（追踪私信对话）
- [ ] id, user_id, account_id, dify_conversation_id, status, message_count, last_message_at

### 4.9 alerts 表
- [ ] id, type, severity, title, message, account_id, is_read, created_at

### 4.10 statistics 表
- [ ] id, date, total_messages_monitored, keyword_triggered_count, dify_triggered_count
- [ ] group_replies_sent, private_messages_sent, new_users_count, active_accounts_count

## 5. Dify 工作流需求

### 5.1 意图分析工作流
- [ ] 输入：message_text, user_id, is_private_chat, conversation_id
- [ ] 输出：is_lead, group_reply_text, private_reply_text, conversation_id
- [ ] 商机判断 + 双回复生成

### 5.2 知识库对话工作流
- [ ] 输入：message_text, user_id, conversation_id
- [ ] 输出：reply_text, conversation_id
- [ ] 多轮对话上下文追踪
