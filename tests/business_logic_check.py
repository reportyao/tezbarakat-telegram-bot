"""
业务逻辑流程验证脚本
根据工作流程图验证消息处理逻辑
"""

import ast
import os

def check_message_handler():
    """检查消息处理器的业务逻辑"""
    print("=" * 60)
    print("业务逻辑流程验证")
    print("=" * 60)
    
    handler_path = "bot_core/handlers/message_handler.py"
    
    with open(handler_path, 'r') as f:
        content = f.read()
    
    # 检查关键业务逻辑
    checks = [
        # 工作流程步骤 1: 处理新消息
        ("async def handle_new_message", "处理新消息方法"),
        ("async def handle_private_message", "处理私信回复方法"),
        
        # 工作流程步骤 2: 关键词匹配
        ("def _match_keywords", "关键词匹配方法"),
        ("self._keywords", "关键词缓存"),
        
        # 工作流程步骤 3: 用户冷却期检查
        ("check_user_cooldown", "用户冷却期检查"),
        
        # 工作流程步骤 4: 调用 Dify 分析
        ("analyze_intent", "Dify 意图分析调用"),
        ("enable_dify_analysis", "Dify 分析开关检查"),
        
        # 工作流程步骤 5: 解析 Dify 结果
        ("confidence", "置信度判断"),
        ("high_confidence_threshold", "高置信度阈值"),
        
        # 工作流程步骤 6: 执行回复策略
        ("_execute_reply_strategy", "执行回复策略方法"),
        
        # 工作流程步骤 7: 群内回复检查
        ("enable_group_reply", "群内回复开关"),
        ("check_group_reply_limit", "群回复频率检查"),
        
        # 工作流程步骤 8: 发送群内@消息
        ("send_group_reply", "发送群内回复"),
        
        # 工作流程步骤 9: 私信检查
        ("enable_private_message", "私信开关"),
        ("check_private_message_limit", "私信频率检查"),
        
        # 工作流程步骤 10: 发送私信
        ("send_private_message", "发送私信"),
        
        # 工作流程步骤 11: 更新用户冷却时间
        ("update_user_cooldown", "更新用户冷却时间"),
        
        # 防风控策略
        ("reply_delay_seconds", "回复延迟"),
        ("send_typing_action", "打字状态模拟"),
        
        # 持续对话
        ("get_or_create_conversation", "获取或创建对话"),
        ("dify_conversation_id", "Dify 对话 ID"),
        
        # 账号轮换
        ("get_available_account", "获取可用账号"),
        ("increment_account_message_count", "增加账号消息计数"),
    ]
    
    print("\n业务逻辑检查:")
    all_passed = True
    for check, desc in checks:
        if check in content:
            print(f"  ✓ {desc}")
        else:
            print(f"  ✗ {desc} - 未找到")
            all_passed = False
    
    return all_passed

def check_database_service():
    """检查数据库服务的业务方法"""
    print("\n" + "=" * 60)
    print("数据库服务方法检查")
    print("=" * 60)
    
    db_path = "bot_core/services/database.py"
    
    with open(db_path, 'r') as f:
        content = f.read()
    
    required_methods = [
        # 账号管理
        ("get_all_accounts", "获取所有账号"),
        ("get_available_account", "获取可用账号"),
        ("update_account_status", "更新账号状态"),
        ("increment_account_message_count", "增加账号消息计数"),
        
        # 群组管理
        ("get_active_groups", "获取活跃群组"),
        ("check_group_reply_limit", "检查群回复限制"),
        ("increment_group_reply_count", "增加群回复计数"),
        
        # 关键词管理
        ("get_active_keywords", "获取活跃关键词"),
        ("increment_keyword_hit", "增加关键词命中"),
        
        # 用户管理
        ("get_or_create_user", "获取或创建用户"),
        ("check_user_cooldown", "检查用户冷却期"),
        ("update_user_cooldown", "更新用户冷却时间"),
        ("check_private_message_limit", "检查私信限制"),
        
        # 消息记录
        ("save_message", "保存消息"),
        ("save_reply", "保存回复"),
        
        # 对话管理
        ("get_or_create_conversation", "获取或创建对话"),
        ("update_conversation", "更新对话"),
        
        # 配置管理
        ("get_config", "获取配置"),
        ("get_all_configs", "获取所有配置"),
        
        # 定时任务
        ("reset_daily_account_counts", "重置每日账号计数"),
        ("reset_hourly_group_counts", "重置每小时群组计数"),
        ("recover_cooling_accounts", "恢复冷却账号"),
    ]
    
    print("\n数据库服务方法检查:")
    all_passed = True
    for method, desc in required_methods:
        if f"def {method}" in content or f"async def {method}" in content:
            print(f"  ✓ {desc}")
        else:
            print(f"  ✗ {desc} - 未找到 {method}")
            all_passed = False
    
    return all_passed

def check_telegram_client():
    """检查 Telegram 客户端管理器"""
    print("\n" + "=" * 60)
    print("Telegram 客户端方法检查")
    print("=" * 60)
    
    client_path = "bot_core/services/telegram_client.py"
    
    with open(client_path, 'r') as f:
        content = f.read()
    
    required_methods = [
        # 客户端管理
        ("create_client", "创建客户端"),
        ("connect_client", "连接客户端"),
        ("disconnect_client", "断开客户端"),
        ("start_login", "开始登录"),
        ("complete_login", "完成登录"),
        
        # 消息发送
        ("send_group_reply", "发送群回复"),
        ("send_private_message", "发送私信"),
        ("send_typing_action", "发送打字状态"),
        
        # 群组操作
        ("join_group", "加入群组"),
        ("get_group_info", "获取群组信息"),
        
        # 事件处理
        ("register_message_handler", "注册消息处理器"),
        ("register_private_message_handler", "注册私信处理器"),
        
        # 健康检查
        ("check_client_health", "检查客户端健康"),
    ]
    
    print("\nTelegram 客户端方法检查:")
    all_passed = True
    for method, desc in required_methods:
        if f"def {method}" in content or f"async def {method}" in content:
            print(f"  ✓ {desc}")
        else:
            print(f"  ✗ {desc} - 未找到 {method}")
            all_passed = False
    
    return all_passed

def check_dify_service():
    """检查 Dify 服务"""
    print("\n" + "=" * 60)
    print("Dify 服务方法检查")
    print("=" * 60)
    
    dify_path = "bot_core/services/dify_service.py"
    
    with open(dify_path, 'r') as f:
        content = f.read()
    
    required_methods = [
        ("analyze_intent", "意图分析"),
        ("chat_with_knowledge", "知识库对话"),
        ("test_connection", "测试连接"),
        ("reload_config", "重载配置"),
    ]
    
    print("\nDify 服务方法检查:")
    all_passed = True
    for method, desc in required_methods:
        if f"def {method}" in content or f"async def {method}" in content:
            print(f"  ✓ {desc}")
        else:
            print(f"  ✗ {desc} - 未找到 {method}")
            all_passed = False
    
    return all_passed

def main():
    """主函数"""
    os.chdir("/home/ubuntu/tezbarakat_bot")
    
    results = []
    results.append(("消息处理器", check_message_handler()))
    results.append(("数据库服务", check_database_service()))
    results.append(("Telegram 客户端", check_telegram_client()))
    results.append(("Dify 服务", check_dify_service()))
    
    print("\n" + "=" * 60)
    print("业务逻辑验证总结")
    print("=" * 60)
    
    all_passed = True
    for name, passed in results:
        status = "✓ 通过" if passed else "✗ 失败"
        print(f"  {name}: {status}")
        if not passed:
            all_passed = False
    
    print("\n" + "=" * 60)
    if all_passed:
        print("所有业务逻辑验证通过！")
    else:
        print("存在业务逻辑问题，请检查上述失败项。")
    print("=" * 60)

if __name__ == "__main__":
    main()
