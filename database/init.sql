-- Tezbarakat Telegram 智能营销机器人 - 数据库初始化脚本
-- 版本: 1.0
-- 数据库: PostgreSQL

-- 创建数据库（如果不存在）
-- CREATE DATABASE tezbarakat_bot;

-- 启用必要的扩展
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- =====================================================
-- 1. accounts - 机器人账号表
-- =====================================================
CREATE TABLE IF NOT EXISTS accounts (
    id SERIAL PRIMARY KEY,
    phone_number VARCHAR(20) UNIQUE NOT NULL,
    session_name VARCHAR(50) NOT NULL,
    status VARCHAR(15) NOT NULL DEFAULT 'logging_in',
    last_used_at TIMESTAMPTZ,
    daily_message_count INTEGER DEFAULT 0,
    daily_reset_date DATE DEFAULT CURRENT_DATE,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW(),
    
    -- 状态约束: logging_in, active, cooling_down, limited, banned
    CONSTRAINT valid_status CHECK (status IN ('logging_in', 'active', 'cooling_down', 'limited', 'banned'))
);

-- 创建索引
CREATE INDEX IF NOT EXISTS idx_accounts_status ON accounts(status);
CREATE INDEX IF NOT EXISTS idx_accounts_last_used ON accounts(last_used_at);

-- =====================================================
-- 2. groups - 监听群组表
-- =====================================================
CREATE TABLE IF NOT EXISTS groups (
    id SERIAL PRIMARY KEY,
    group_id BIGINT UNIQUE NOT NULL,
    group_name VARCHAR(255),
    group_username VARCHAR(255),
    is_active BOOLEAN DEFAULT TRUE,
    hourly_reply_count INTEGER DEFAULT 0,
    hourly_reset_time TIMESTAMPTZ DEFAULT NOW(),
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- 创建索引
CREATE INDEX IF NOT EXISTS idx_groups_active ON groups(is_active);
CREATE INDEX IF NOT EXISTS idx_groups_group_id ON groups(group_id);

-- =====================================================
-- 3. keywords - 关键词表
-- =====================================================
CREATE TABLE IF NOT EXISTS keywords (
    id SERIAL PRIMARY KEY,
    keyword VARCHAR(100) UNIQUE NOT NULL,
    is_active BOOLEAN DEFAULT TRUE,
    hit_count INTEGER DEFAULT 0,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- 创建索引
CREATE INDEX IF NOT EXISTS idx_keywords_active ON keywords(is_active);

-- =====================================================
-- 4. users - 目标用户表
-- =====================================================
CREATE TABLE IF NOT EXISTS users (
    user_id BIGINT PRIMARY KEY,
    username VARCHAR(255),
    first_name VARCHAR(255),
    last_name VARCHAR(255),
    last_private_message_time TIMESTAMPTZ,
    total_messages_received INTEGER DEFAULT 0,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- 创建索引
CREATE INDEX IF NOT EXISTS idx_users_last_pm ON users(last_private_message_time);

-- =====================================================
-- 5. messages - 监听消息记录表
-- =====================================================
CREATE TABLE IF NOT EXISTS messages (
    id BIGSERIAL PRIMARY KEY,
    timestamp TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    group_id BIGINT NOT NULL,
    user_id BIGINT NOT NULL,
    message_id BIGINT,
    text TEXT,
    triggered_keyword BOOLEAN DEFAULT FALSE,
    matched_keyword VARCHAR(100),
    triggered_dify BOOLEAN DEFAULT FALSE,
    dify_confidence FLOAT,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- 创建索引
CREATE INDEX IF NOT EXISTS idx_messages_timestamp ON messages(timestamp DESC);
CREATE INDEX IF NOT EXISTS idx_messages_group ON messages(group_id);
CREATE INDEX IF NOT EXISTS idx_messages_user ON messages(user_id);
CREATE INDEX IF NOT EXISTS idx_messages_triggered ON messages(triggered_keyword, triggered_dify);

-- =====================================================
-- 6. replies - 回复记录表
-- =====================================================
CREATE TABLE IF NOT EXISTS replies (
    id BIGSERIAL PRIMARY KEY,
    timestamp TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    account_id INTEGER REFERENCES accounts(id) ON DELETE SET NULL,
    user_id BIGINT NOT NULL,
    group_id BIGINT,
    type VARCHAR(10) NOT NULL,
    sent_text TEXT,
    conversation_id VARCHAR(255),
    status VARCHAR(20) DEFAULT 'sent',
    error_message TEXT,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    
    -- 类型约束: group, private
    CONSTRAINT valid_reply_type CHECK (type IN ('group', 'private'))
);

-- 创建索引
CREATE INDEX IF NOT EXISTS idx_replies_timestamp ON replies(timestamp DESC);
CREATE INDEX IF NOT EXISTS idx_replies_account ON replies(account_id);
CREATE INDEX IF NOT EXISTS idx_replies_user ON replies(user_id);
CREATE INDEX IF NOT EXISTS idx_replies_type ON replies(type);

-- =====================================================
-- 7. conversations - 对话记录表（用于追踪私信对话）
-- =====================================================
CREATE TABLE IF NOT EXISTS conversations (
    id SERIAL PRIMARY KEY,
    user_id BIGINT NOT NULL,
    account_id INTEGER REFERENCES accounts(id) ON DELETE SET NULL,
    dify_conversation_id VARCHAR(255),
    status VARCHAR(20) DEFAULT 'active',
    message_count INTEGER DEFAULT 0,
    last_message_at TIMESTAMPTZ DEFAULT NOW(),
    created_at TIMESTAMPTZ DEFAULT NOW(),
    
    CONSTRAINT valid_conv_status CHECK (status IN ('active', 'closed', 'expired'))
);

-- 创建索引
CREATE INDEX IF NOT EXISTS idx_conversations_user ON conversations(user_id);
CREATE INDEX IF NOT EXISTS idx_conversations_status ON conversations(status);

-- =====================================================
-- 8. app_config - 应用配置表
-- =====================================================
CREATE TABLE IF NOT EXISTS app_config (
    key VARCHAR(50) PRIMARY KEY,
    value JSONB NOT NULL,
    description TEXT,
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- 插入默认配置
INSERT INTO app_config (key, value, description) VALUES
    ('private_message_interval_minutes', '5', '同一账号对不同用户发送私信的最小间隔（分钟）'),
    ('user_cooldown_days', '3', '对同一用户的私信间隔（天）'),
    ('daily_private_message_limit', '20', '单账号每日私信上限'),
    ('hourly_group_reply_limit', '3', '单群每小时回复上限'),
    ('dify_confidence_threshold', '0.7', 'Dify 置信度阈值'),
    ('active_hours_start', '8', '活跃时段开始（小时，塔吉克斯坦时间）'),
    ('active_hours_end', '24', '活跃时段结束（小时，塔吉克斯坦时间）'),
    ('reply_delay_min_seconds', '10', '回复延迟最小秒数'),
    ('reply_delay_max_seconds', '60', '回复延迟最大秒数'),
    ('typing_duration_min_seconds', '2', '打字状态最小持续秒数'),
    ('typing_duration_max_seconds', '5', '打字状态最大持续秒数'),
    ('enable_group_reply', 'true', '是否启用群内回复'),
    ('enable_private_message', 'true', '是否启用私信'),
    ('dify_api_url', '"http://localhost/v1"', 'Dify API 地址'),
    ('dify_api_key', '""', 'Dify API 密钥'),
    ('dify_workflow_id', '""', 'Dify 工作流 ID'),
    ('dify_knowledge_workflow_id', '""', 'Dify 知识库工作流 ID'),
    ('telegram_api_id', '""', 'Telegram API ID'),
    ('telegram_api_hash', '""', 'Telegram API Hash'),
    ('enable_dify_analysis', 'true', '是否启用 Dify 意图分析'),
    ('group_reply_template', '"您好 {username}！感谢您的咨询，我们的专业顾问会尽快与您联系。"', '群内回复模板'),
    ('private_reply_template', '"您好！感谢您对我们服务的关注。我是 Tezbarakat 的客服，很高兴为您服务。请问有什么可以帮助您的？"', '私信回复模板')
ON CONFLICT (key) DO NOTHING;

-- =====================================================
-- 9. alerts - 告警记录表
-- =====================================================
CREATE TABLE IF NOT EXISTS alerts (
    id SERIAL PRIMARY KEY,
    type VARCHAR(50) NOT NULL,
    severity VARCHAR(20) NOT NULL DEFAULT 'info',
    title VARCHAR(255) NOT NULL,
    message TEXT,
    account_id INTEGER REFERENCES accounts(id) ON DELETE SET NULL,
    is_read BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    
    CONSTRAINT valid_severity CHECK (severity IN ('info', 'warning', 'error', 'critical'))
);

-- 创建索引
CREATE INDEX IF NOT EXISTS idx_alerts_created ON alerts(created_at DESC);
CREATE INDEX IF NOT EXISTS idx_alerts_unread ON alerts(is_read) WHERE is_read = FALSE;

-- =====================================================
-- 10. statistics - 统计数据表（用于仪表盘）
-- =====================================================
CREATE TABLE IF NOT EXISTS statistics (
    id SERIAL PRIMARY KEY,
    date DATE NOT NULL DEFAULT CURRENT_DATE,
    total_messages_monitored INTEGER DEFAULT 0,
    keyword_triggered_count INTEGER DEFAULT 0,
    dify_triggered_count INTEGER DEFAULT 0,
    group_replies_sent INTEGER DEFAULT 0,
    private_messages_sent INTEGER DEFAULT 0,
    new_users_count INTEGER DEFAULT 0,
    active_accounts_count INTEGER DEFAULT 0,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    
    CONSTRAINT unique_date UNIQUE (date)
);

-- 创建索引
CREATE INDEX IF NOT EXISTS idx_statistics_date ON statistics(date DESC);

-- =====================================================
-- 触发器函数：自动更新 updated_at 字段
-- =====================================================
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- 为 accounts 表添加触发器
DROP TRIGGER IF EXISTS update_accounts_updated_at ON accounts;
CREATE TRIGGER update_accounts_updated_at
    BEFORE UPDATE ON accounts
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

-- 为 app_config 表添加触发器
DROP TRIGGER IF EXISTS update_app_config_updated_at ON app_config;
CREATE TRIGGER update_app_config_updated_at
    BEFORE UPDATE ON app_config
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

-- =====================================================
-- 视图：账号状态统计
-- =====================================================
CREATE OR REPLACE VIEW account_status_summary AS
SELECT 
    status,
    COUNT(*) as count
FROM accounts
GROUP BY status;

-- =====================================================
-- 视图：今日统计
-- =====================================================
CREATE OR REPLACE VIEW today_statistics AS
SELECT 
    COALESCE(s.total_messages_monitored, 0) as total_messages,
    COALESCE(s.keyword_triggered_count, 0) as keyword_triggers,
    COALESCE(s.dify_triggered_count, 0) as dify_triggers,
    COALESCE(s.group_replies_sent, 0) as group_replies,
    COALESCE(s.private_messages_sent, 0) as private_messages,
    COALESCE(s.new_users_count, 0) as new_users,
    (SELECT COUNT(*) FROM accounts WHERE status = 'active') as active_accounts,
    (SELECT COUNT(*) FROM accounts WHERE status = 'banned') as banned_accounts,
    (SELECT COUNT(*) FROM groups WHERE is_active = TRUE) as active_groups,
    (SELECT COUNT(*) FROM keywords WHERE is_active = TRUE) as active_keywords,
    (SELECT COUNT(*) FROM alerts WHERE is_read = FALSE AND created_at > NOW() - INTERVAL '24 hours') as unread_alerts
FROM statistics s
WHERE s.date = CURRENT_DATE;

-- 确保今日统计记录存在
INSERT INTO statistics (date) VALUES (CURRENT_DATE) ON CONFLICT (date) DO NOTHING;

COMMENT ON TABLE accounts IS '机器人账号表，存储所有用于发送消息的Telegram小号信息';
COMMENT ON TABLE groups IS '监听群组表，存储需要监控的Telegram群组';
COMMENT ON TABLE keywords IS '关键词表，用于触发消息处理的关键词列表';
COMMENT ON TABLE users IS '目标用户表，记录所有被机器人接触过的用户';
COMMENT ON TABLE messages IS '消息记录表，存储所有监听到的群组消息';
COMMENT ON TABLE replies IS '回复记录表，存储所有机器人发送的回复';
COMMENT ON TABLE conversations IS '对话记录表，追踪与用户的私信对话';
COMMENT ON TABLE app_config IS '应用配置表，存储可动态修改的系统配置';
COMMENT ON TABLE alerts IS '告警记录表，存储系统告警信息';
COMMENT ON TABLE statistics IS '统计数据表，按日存储系统运行统计';
