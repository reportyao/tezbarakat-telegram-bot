"""
API 端点完整性检查脚本
对照前端 API 调用和后端 API 端点
"""

# 后端 API 端点列表
BACKEND_ENDPOINTS = {
    # 认证
    "POST /auth/login": "登录",
    "POST /auth/logout": "登出",
    "GET /auth/me": "获取当前用户",
    
    # Bot 控制
    "GET /bot/status": "获取 Bot 状态",
    "POST /bot/control": "控制 Bot",
    "POST /bot/test-dify": "测试 Dify 连接",
    
    # 仪表盘
    "GET /dashboard": "获取仪表盘数据",
    "GET /dashboard/stats": "获取统计数据",
    "GET /dashboard/statistics": "获取历史统计",
    "GET /dashboard/chart/messages": "获取消息图表数据",
    "GET /dashboard/chart/replies": "获取回复图表数据",
    
    # 账号管理
    "GET /accounts": "获取所有账号",
    "POST /accounts": "创建账号",
    "GET /accounts/{id}": "获取单个账号",
    "PUT /accounts/{id}/status": "更新账号状态",
    "DELETE /accounts/{id}": "删除账号",
    "POST /accounts/{id}/login/start": "开始登录",
    "POST /accounts/{id}/login/complete": "完成登录",
    "POST /accounts/{id}/reconnect": "重新连接",
    "GET /accounts/{id}/health": "健康检查",
    
    # 群组管理
    "GET /groups": "获取所有群组",
    "GET /groups/resolve": "解析群组",
    "POST /groups": "创建群组",
    "GET /groups/{id}": "获取单个群组",
    "PUT /groups/{id}": "更新群组",
    "DELETE /groups/{id}": "删除群组",
    "POST /groups/{id}/refresh": "刷新群组信息",
    
    # 关键词管理
    "GET /keywords": "获取所有关键词",
    "POST /keywords": "创建关键词",
    "POST /keywords/batch": "批量创建关键词",
    "GET /keywords/{id}": "获取单个关键词",
    "PUT /keywords/{id}": "更新关键词",
    "DELETE /keywords/{id}": "删除关键词",
    "GET /keywords/stats/top": "获取热门关键词",
    
    # 消息记录
    "GET /messages": "获取消息列表",
    "GET /replies": "获取回复列表",
    "GET /users": "获取用户列表",
    "GET /users/{id}": "获取单个用户",
    "GET /users/{id}/messages": "获取用户消息",
    "GET /users/{id}/replies": "获取用户回复",
    
    # 配置管理
    "GET /config": "获取所有配置",
    "GET /config/{key}": "获取单个配置",
    "PUT /config/{key}": "更新单个配置",
    "PUT /config": "批量更新配置",
    
    # 告警管理
    "GET /alerts": "获取告警列表",
    "POST /alerts/read": "标记已读",
    "POST /alerts/read-all": "全部标记已读",
    
    # WebSocket
    "GET /ws": "WebSocket 连接",
    "GET /ws/connections": "获取连接数",
    
    # 健康检查
    "GET /health": "健康检查",
    "GET /": "根路径",
}

# 前端 API 调用列表
FRONTEND_API_CALLS = {
    # 认证
    "POST /auth/login": "authApi.login",
    "POST /auth/logout": "authApi.logout",
    "GET /auth/me": "authApi.getCurrentUser",
    
    # Bot 控制
    "GET /bot/status": "dashboardApi.getBotStatus",
    "POST /bot/control": "dashboardApi.controlBot",
    "POST /bot/test-dify": "dashboardApi.testDify",
    
    # 仪表盘
    "GET /dashboard": "dashboardApi.getData",
    
    # 账号管理
    "GET /accounts": "accountsApi.getAll",
    "POST /accounts": "accountsApi.create",
    "POST /accounts/{id}/login/start": "accountsApi.startLogin",
    "POST /accounts/{id}/login/complete": "accountsApi.completeLogin",
    "POST /accounts/{id}/reconnect": "accountsApi.reconnect",
    "GET /accounts/{id}/health": "accountsApi.checkHealth",
    "DELETE /accounts/{id}": "accountsApi.delete",
    
    # 群组管理
    "GET /groups": "groupsApi.getAll",
    "GET /groups/resolve": "groupsApi.resolve",
    "POST /groups": "groupsApi.create",
    "PUT /groups/{id}": "groupsApi.update",
    "DELETE /groups/{id}": "groupsApi.delete",
    
    # 关键词管理
    "GET /keywords": "keywordsApi.getAll",
    "POST /keywords": "keywordsApi.create",
    "POST /keywords/batch": "keywordsApi.batchCreate",
    "PUT /keywords/{id}": "keywordsApi.update",
    "DELETE /keywords/{id}": "keywordsApi.delete",
    
    # 消息记录
    "GET /messages": "messagesApi.getMessages",
    "GET /replies": "messagesApi.getReplies",
    "GET /users": "messagesApi.getUsers",
    
    # 配置管理
    "GET /config": "configApi.getAll",
    "PUT /config/{key}": "configApi.update",
    "PUT /config": "configApi.batchUpdate",
    
    # 告警管理
    "GET /alerts": "alertsApi.getAll",
    "POST /alerts/read": "alertsApi.markRead",
    "POST /alerts/read-all": "alertsApi.markAllRead",
}

def check_api_coverage():
    """检查 API 覆盖率"""
    print("=" * 60)
    print("API 端点完整性检查")
    print("=" * 60)
    
    # 检查后端端点是否都有前端调用
    missing_frontend = []
    for endpoint, desc in BACKEND_ENDPOINTS.items():
        if endpoint not in FRONTEND_API_CALLS:
            # 跳过一些不需要前端调用的端点
            if any(skip in endpoint for skip in ["/health", "GET /", "/ws/connections", "/stats", "/chart/", "/statistics"]):
                continue
            if "{id}" in endpoint:
                # 检查是否有通用版本
                generic = endpoint.replace("{id}", "{key}") if "config" in endpoint else endpoint
                if generic not in FRONTEND_API_CALLS:
                    missing_frontend.append(f"{endpoint} ({desc})")
            else:
                missing_frontend.append(f"{endpoint} ({desc})")
    
    # 检查前端调用是否都有后端端点
    missing_backend = []
    for endpoint, func in FRONTEND_API_CALLS.items():
        if endpoint not in BACKEND_ENDPOINTS:
            # 检查是否有参数化版本
            found = False
            for be in BACKEND_ENDPOINTS:
                if "{" in be:
                    pattern = be.replace("{id}", "\\{id\\}").replace("{key}", "\\{key\\}")
                    if endpoint.replace("{id}", "\\{id\\}").replace("{key}", "\\{key\\}") == pattern:
                        found = True
                        break
            if not found:
                missing_backend.append(f"{endpoint} ({func})")
    
    print("\n后端端点未被前端调用:")
    if missing_frontend:
        for item in missing_frontend:
            print(f"  - {item}")
    else:
        print("  无")
    
    print("\n前端调用缺少后端端点:")
    if missing_backend:
        for item in missing_backend:
            print(f"  - {item}")
    else:
        print("  无")
    
    # 计算覆盖率
    total_backend = len(BACKEND_ENDPOINTS)
    covered = total_backend - len(missing_frontend)
    coverage = (covered / total_backend) * 100
    
    print(f"\n后端端点总数: {total_backend}")
    print(f"前端调用覆盖: {covered}")
    print(f"覆盖率: {coverage:.1f}%")
    print("=" * 60)

if __name__ == "__main__":
    check_api_coverage()
