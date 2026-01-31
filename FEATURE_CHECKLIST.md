# Tezbarakat Telegram Bot - 功能需求检查清单

## 1. 核心功能需求

### 1.1 多群组实时监控
- [x] 同时监控多达100个群组
- [x] 使用主监听账号接入所有目标群组

### 1.2 智能意图识别
- [x] 关键词触发（支持塔吉克语、俄语，不区分大小写）
- [x] Dify AI 工作流意图分析
- [x] 置信度阈值判断
- [x] 可选择禁用 Dify 分析，使用模板回复

### 1.3 双层回复策略
- [x] 群内@用户进行简短互动（引用原消息）
- [x] 私信发送详细平台介绍
- [x] 一次 Dify 调用生成两种回复文本
- [x] 支持模板回复（禁用 Dify 时）

### 1.4 多账号防风控
- [x] 最多20个小号轮换
- [x] 账号状态机管理 (logging_in, active, cooling_down, limited, banned)
- [x] 优先选择 last_used_at 最早的账号

### 1.5 持续对话能力
- [x] 监听用户私信回复
- [x] 调用 Dify 知识库进行多轮对话
- [x] 使用 conversation_id 追踪上下文

### 1.6 可视化 Web 管理后台
- [x] 仪表盘（核心指标、账号状态图、告警、实时日志）
- [x] 账号管理（列表、添加、登录流程）
- [x] 群组管理（增删改查、启用/禁用）
- [x] 关键词管理（增删改查、启用/禁用、批量导入）
- [x] 系统配置（动态修改配置项）
- [x] 消息记录查询
- [x] 用户列表查询

### 1.7 动态配置管理
- [x] 无需重启服务即可添加/移除群组
- [x] 无需重启服务即可添加/移除关键词
- [x] 配置变更实时通知 Bot 核心服务

### 1.8 异常告警
- [x] 账号封禁告警
- [x] API 失败告警
- [x] WebSocket 实时推送告警

## 2. 防风控策略

### 2.1 频率控制
- [x] 单账号私信间隔 ≥ 5 分钟（可配置）
- [x] 单账号每日私信上限 20 条（可配置）
- [x] 单群每小时回复上限 3 条（可配置）
- [x] 用户冷却期 3 天（可配置）

### 2.2 真人模拟行为
- [x] 打字状态模拟（2-5秒随机，可配置）
- [x] 发送延迟随机化（10-60秒，可配置）
- [x] 活跃时段控制（早8点至晚12点，塔吉克斯坦时间，可配置）

### 2.3 账号状态自动检测
- [x] FloodWaitError 处理（设为 limited，等待后恢复）
- [x] UserBannedInChannelError / ChatWriteForbiddenError 处理
- [x] AuthKeyUnregisteredError 处理（设为 banned，发出告警）
- [x] 心跳检测（定期检测账号有效性）
- [x] 每日自动恢复 cooling_down 状态的账号

## 3. API 端点需求

### 3.1 后端 API
- [x] GET /api/dashboard - 聚合统计数据
- [x] GET /api/accounts - 获取所有账号
- [x] POST /api/accounts - 创建新账号
- [x] POST /api/accounts/{id}/login/start - 开始登录流程
- [x] POST /api/accounts/{id}/login/complete - 完成登录（验证码/密码）
- [x] POST /api/accounts/{id}/reconnect - 重新连接账号
- [x] GET /api/accounts/{id}/health - 检查账号健康
- [x] DELETE /api/accounts/{id} - 删除账号
- [x] GET/POST/PUT/DELETE /api/groups - 群组管理
- [x] GET /api/groups/resolve - 解析群组用户名
- [x] GET/POST/PUT/DELETE /api/keywords - 关键词管理
- [x] POST /api/keywords/batch - 批量创建关键词
- [x] GET /api/messages - 消息记录查询
- [x] GET /api/replies - 回复记录查询
- [x] GET /api/users - 用户列表查询
- [x] GET /api/config - 获取配置
- [x] PUT /api/config - 批量更新配置
- [x] PUT /api/config/{key} - 更新单个配置
- [x] GET /api/alerts - 获取告警列表
- [x] POST /api/alerts/read - 标记告警已读
- [x] POST /api/alerts/read-all - 标记所有告警已读
- [x] GET /api/bot/status - 获取 Bot 状态
- [x] POST /api/bot/control - 控制 Bot（启动/停止/重启）
- [x] POST /api/bot/test-dify - 测试 Dify 连接
- [x] WebSocket /ws/logs - 实时日志推送
- [x] WebSocket /ws/alerts - 实时告警推送

### 3.2 Bot 核心内部 API
- [x] GET /health - 健康检查
- [x] POST /start - 启动 Bot
- [x] POST /stop - 停止 Bot
- [x] GET /status - 获取状态
- [x] POST /accounts/login/start - 开始登录
- [x] POST /accounts/login/complete - 完成登录
- [x] DELETE /accounts/{phone} - 移除账号
- [x] POST /accounts/reconnect - 重新连接账号
- [x] GET /accounts/{phone}/health - 检查账号健康
- [x] GET /groups/resolve - 解析群组
- [x] GET /groups/{group_id}/info - 获取群组信息
- [x] POST /groups/add - 添加群组
- [x] POST /groups/remove - 移除群组
- [x] POST /keywords/reload - 重新加载关键词
- [x] POST /config/reload - 重新加载配置
- [x] GET /dify/test - 测试 Dify 连接

## 4. 数据库表需求

### 4.1 accounts 表
- [x] id, phone_number, session_name, status, last_used_at, created_at, updated_at
- [x] daily_message_count, daily_reset_date（每日私信计数）

### 4.2 groups 表
- [x] id, group_id, group_name, group_username, is_active, created_at
- [x] hourly_reply_count, hourly_reset_time（每小时回复计数）

### 4.3 keywords 表
- [x] id, keyword, is_active, created_at
- [x] hit_count（命中计数）

### 4.4 messages 表
- [x] id, timestamp, group_id, user_id, text, triggered_keyword, triggered_dify
- [x] message_id, matched_keyword, dify_confidence, created_at

### 4.5 replies 表
- [x] id, timestamp, account_id, user_id, group_id, type, sent_text, conversation_id
- [x] status, error_message, created_at

### 4.6 users 表
- [x] user_id, username, last_private_message_time, created_at
- [x] first_name, last_name, total_messages_received

### 4.7 app_config 表
- [x] key, value (JSONB), description, updated_at

### 4.8 conversations 表（追踪私信对话）
- [x] id, user_id, account_id, dify_conversation_id, status, message_count, last_message_at, created_at

### 4.9 alerts 表
- [x] id, type, severity, title, message, account_id, is_read, created_at

### 4.10 statistics 表
- [x] id, date, total_messages_monitored, keyword_triggered_count, dify_triggered_count
- [x] group_replies_sent, private_messages_sent, new_users_count, active_accounts_count

## 5. Dify 工作流需求

### 5.1 意图分析工作流
- [x] 输入：message_text, user_id, username
- [x] 输出：is_opportunity, confidence, group_reply, private_reply, category
- [x] 商机判断 + 双回复生成

### 5.2 知识库对话工作流
- [x] 输入：message_text, user_id, conversation_id
- [x] 输出：reply_text, conversation_id
- [x] 多轮对话上下文追踪

## 6. 前端页面需求

### 6.1 登录页面
- [x] 用户名/密码登录
- [x] JWT Token 认证

### 6.2 仪表盘页面
- [x] Bot 状态卡片（运行状态、运行时间、连接账号数、监听群组数）
- [x] 今日统计卡片（监控消息数、关键词触发、Dify 触发、群内回复、私信发送、新用户）
- [x] 账号状态饼图
- [x] 近7天趋势图
- [x] 最近告警列表

### 6.3 账号管理页面
- [x] 账号列表（状态、最后使用时间、今日消息数）
- [x] 添加账号（手机号、Session 名称）
- [x] 登录流程（验证码、两步验证密码）
- [x] 重新连接、健康检查、删除

### 6.4 群组管理页面
- [x] 群组列表（名称、ID、状态、每小时回复数）
- [x] 添加群组（通过用户名解析）
- [x] 启用/禁用、删除

### 6.5 关键词管理页面
- [x] 关键词列表（关键词、命中次数、状态）
- [x] 添加关键词
- [x] 批量导入关键词
- [x] 启用/禁用、删除

### 6.6 消息记录页面
- [x] 消息列表（时间、群组、用户、内容、触发状态）
- [x] 回复列表（时间、账号、用户、类型、内容、状态）
- [x] 筛选和分页

### 6.7 用户列表页面
- [x] 用户列表（用户ID、用户名、姓名、最后私信时间、收到消息数）
- [x] 分页

### 6.8 实时日志页面
- [x] WebSocket 实时日志流
- [x] 日志级别筛选
- [x] 自动滚动

### 6.9 系统配置页面
- [x] 功能开关（群内回复、私信、Dify 分析）
- [x] 频率限制配置
- [x] 时间配置
- [x] Dify 配置
- [x] 回复模板配置
- [x] 批量保存

## 7. 部署需求

### 7.1 Docker 容器化
- [x] web_backend Dockerfile
- [x] bot_core Dockerfile
- [x] web_frontend Dockerfile（Nginx）
- [x] docker-compose.yml（PostgreSQL、后端、Bot核心、前端）

### 7.2 配置管理
- [x] .env.example 环境变量模板
- [x] 数据库初始化脚本（表结构、默认配置）

### 7.3 健康检查
- [x] 后端健康检查端点
- [x] Bot 核心健康检查端点
- [x] Docker 健康检查配置
