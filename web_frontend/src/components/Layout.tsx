import React, { useEffect } from 'react';
import { Link, useLocation, useNavigate, Outlet } from 'react-router-dom';
import {
  LayoutDashboard,
  Users,
  MessageSquare,
  Key,
  Settings,
  LogOut,
  Menu,
  Bell,
  Activity,
  UserCircle,
  ScrollText,
  Hash,
} from 'lucide-react';
import { useAppStore } from '@/store';
import { wsService } from '@/services/websocket';
import { cn } from '@/utils';
import type { WSMessage } from '@/types';

const navigation = [
  { name: '仪表盘', href: '/', icon: LayoutDashboard },
  { name: '账号管理', href: '/accounts', icon: Users },
  { name: '群组管理', href: '/groups', icon: Hash },
  { name: '关键词管理', href: '/keywords', icon: Key },
  { name: '消息记录', href: '/messages', icon: MessageSquare },
  { name: '用户列表', href: '/users', icon: UserCircle },
  { name: '实时日志', href: '/logs', icon: ScrollText },
  { name: '系统配置', href: '/config', icon: Settings },
];

export default function Layout() {
  const location = useLocation();
  const navigate = useNavigate();
  const {
    sidebarOpen,
    setSidebarOpen,
    unreadAlerts,
    setAuthenticated,
    addLog,
    addAlert,
    setBotStatus,
  } = useAppStore();

  useEffect(() => {
    // 连接 WebSocket
    wsService.connect();

    // 订阅消息
    const unsubscribe = wsService.subscribe((message: WSMessage) => {
      switch (message.type) {
        case 'log':
          addLog(message.data);
          break;
        case 'alert':
          addAlert(message.data);
          break;
        case 'status':
          setBotStatus(message.data);
          break;
      }
    });

    return () => {
      unsubscribe();
      wsService.disconnect();
    };
  }, []);

  const handleLogout = () => {
    localStorage.removeItem('token');
    setAuthenticated(false);
    navigate('/login');
  };

  return (
    <div className="min-h-screen bg-gray-100">
      {/* 侧边栏 */}
      <aside
        className={cn(
          'fixed inset-y-0 left-0 z-50 w-64 bg-white shadow-lg transform transition-transform duration-300 ease-in-out',
          sidebarOpen ? 'translate-x-0' : '-translate-x-full'
        )}
      >
        <div className="flex flex-col h-full">
          {/* Logo */}
          <div className="flex items-center justify-center h-16 bg-primary-600">
            <Activity className="w-8 h-8 text-white" />
            <span className="ml-2 text-xl font-bold text-white">Tezbarakat</span>
          </div>

          {/* 导航菜单 */}
          <nav className="flex-1 px-4 py-4 space-y-1 overflow-y-auto">
            {navigation.map((item) => {
              const isActive = location.pathname === item.href;
              return (
                <Link
                  key={item.name}
                  to={item.href}
                  className={cn(
                    'flex items-center px-4 py-3 text-sm font-medium rounded-lg transition-colors',
                    isActive
                      ? 'bg-primary-50 text-primary-700'
                      : 'text-gray-600 hover:bg-gray-50 hover:text-gray-900'
                  )}
                >
                  <item.icon className="w-5 h-5 mr-3" />
                  {item.name}
                </Link>
              );
            })}
          </nav>

          {/* 退出按钮 */}
          <div className="p-4 border-t">
            <button
              onClick={handleLogout}
              className="flex items-center w-full px-4 py-3 text-sm font-medium text-gray-600 rounded-lg hover:bg-gray-50 hover:text-gray-900 transition-colors"
            >
              <LogOut className="w-5 h-5 mr-3" />
              退出登录
            </button>
          </div>
        </div>
      </aside>

      {/* 主内容区 */}
      <div
        className={cn(
          'transition-all duration-300 ease-in-out',
          sidebarOpen ? 'ml-64' : 'ml-0'
        )}
      >
        {/* 顶部导航栏 */}
        <header className="sticky top-0 z-40 bg-white shadow-sm">
          <div className="flex items-center justify-between h-16 px-4">
            <button
              onClick={() => setSidebarOpen(!sidebarOpen)}
              className="p-2 text-gray-500 rounded-lg hover:bg-gray-100"
            >
              <Menu className="w-6 h-6" />
            </button>

            <div className="flex items-center space-x-4">
              {/* 告警按钮 */}
              <Link
                to="/alerts"
                className="relative p-2 text-gray-500 rounded-lg hover:bg-gray-100"
              >
                <Bell className="w-6 h-6" />
                {unreadAlerts > 0 && (
                  <span className="absolute top-0 right-0 flex items-center justify-center w-5 h-5 text-xs font-bold text-white bg-red-500 rounded-full">
                    {unreadAlerts > 99 ? '99+' : unreadAlerts}
                  </span>
                )}
              </Link>
            </div>
          </div>
        </header>

        {/* 页面内容 */}
        <main className="p-6">
          <Outlet />
        </main>
      </div>
    </div>
  );
}
