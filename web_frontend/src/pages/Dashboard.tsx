import React from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import {
  Activity,
  Users,
  MessageSquare,
  Send,
  UserPlus,
  AlertTriangle,
  Play,
  Square,
  RefreshCw,
} from 'lucide-react';
import {
  LineChart,
  Line,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
  BarChart,
  Bar,
} from 'recharts';
import { dashboardApi } from '@/services/api';
import { useAppStore } from '@/store';
import { formatUptime, formatDateTime, formatNumber } from '@/utils';
import { Button, Card, CardHeader, CardContent, Badge, Loading } from '@/components/ui';

export default function Dashboard() {
  const queryClient = useQueryClient();
  const setBotStatus = useAppStore((state) => state.setBotStatus);

  // 获取仪表盘数据
  const { data, isLoading, error } = useQuery({
    queryKey: ['dashboard'],
    queryFn: dashboardApi.getData,
    refetchInterval: 30000, // 每30秒刷新
  });

  // Bot 控制
  const controlMutation = useMutation({
    mutationFn: dashboardApi.controlBot,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['dashboard'] });
    },
  });

  if (isLoading) return <Loading />;
  if (error) return <div className="text-red-500">加载失败</div>;
  if (!data) return null;

  const { bot_status, today_stats, recent_stats, account_status, recent_alerts } = data;

  // 更新全局状态
  setBotStatus(bot_status);

  // 统计卡片数据
  const statsCards = [
    {
      title: '今日监控消息',
      value: today_stats?.total_messages_monitored || 0,
      icon: MessageSquare,
      color: 'text-blue-600',
      bgColor: 'bg-blue-100',
    },
    {
      title: '关键词触发',
      value: today_stats?.keyword_triggered_count || 0,
      icon: Activity,
      color: 'text-green-600',
      bgColor: 'bg-green-100',
    },
    {
      title: '群内回复',
      value: today_stats?.group_replies_sent || 0,
      icon: Send,
      color: 'text-purple-600',
      bgColor: 'bg-purple-100',
    },
    {
      title: '私信发送',
      value: today_stats?.private_messages_sent || 0,
      icon: UserPlus,
      color: 'text-orange-600',
      bgColor: 'bg-orange-100',
    },
  ];

  return (
    <div className="space-y-6 animate-fadeIn">
      {/* 页面标题 */}
      <div className="flex items-center justify-between">
        <h1 className="text-2xl font-bold text-gray-900">仪表盘</h1>
        <div className="flex items-center space-x-2">
          {bot_status.running ? (
            <>
              <Button
                variant="danger"
                onClick={() => controlMutation.mutate('stop')}
                loading={controlMutation.isPending}
              >
                <Square className="w-4 h-4 mr-2" />
                停止
              </Button>
              <Button
                variant="secondary"
                onClick={() => controlMutation.mutate('restart')}
                loading={controlMutation.isPending}
              >
                <RefreshCw className="w-4 h-4 mr-2" />
                重启
              </Button>
            </>
          ) : (
            <Button
              variant="primary"
              onClick={() => controlMutation.mutate('start')}
              loading={controlMutation.isPending}
            >
              <Play className="w-4 h-4 mr-2" />
              启动
            </Button>
          )}
        </div>
      </div>

      {/* Bot 状态卡片 */}
      <Card>
        <CardContent className="py-4">
          <div className="flex items-center justify-between">
            <div className="flex items-center space-x-4">
              <div
                className={`w-3 h-3 rounded-full ${
                  bot_status.running ? 'bg-green-500 animate-pulse' : 'bg-gray-400'
                }`}
              />
              <div>
                <p className="text-sm text-gray-500">Bot 状态</p>
                <p className="text-lg font-semibold">
                  {bot_status.running ? '运行中' : '已停止'}
                </p>
              </div>
            </div>
            <div className="grid grid-cols-3 gap-8">
              <div className="text-center">
                <p className="text-sm text-gray-500">运行时间</p>
                <p className="text-lg font-semibold">
                  {bot_status.uptime ? formatUptime(bot_status.uptime) : '-'}
                </p>
              </div>
              <div className="text-center">
                <p className="text-sm text-gray-500">连接账号</p>
                <p className="text-lg font-semibold">{bot_status.connected_accounts}</p>
              </div>
              <div className="text-center">
                <p className="text-sm text-gray-500">监听群组</p>
                <p className="text-lg font-semibold">{bot_status.monitored_groups}</p>
              </div>
            </div>
          </div>
        </CardContent>
      </Card>

      {/* 统计卡片 */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
        {statsCards.map((stat) => (
          <Card key={stat.title}>
            <CardContent className="py-4">
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-sm text-gray-500">{stat.title}</p>
                  <p className="text-2xl font-bold mt-1">{formatNumber(stat.value)}</p>
                </div>
                <div className={`p-3 rounded-full ${stat.bgColor}`}>
                  <stat.icon className={`w-6 h-6 ${stat.color}`} />
                </div>
              </div>
            </CardContent>
          </Card>
        ))}
      </div>

      {/* 图表区域 */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* 消息趋势图 */}
        <Card>
          <CardHeader>
            <h3 className="text-lg font-semibold">消息趋势（近7天）</h3>
          </CardHeader>
          <CardContent>
            <div className="h-64">
              <ResponsiveContainer width="100%" height="100%">
                <LineChart data={recent_stats || []}>
                  <CartesianGrid strokeDasharray="3 3" />
                  <XAxis dataKey="date" />
                  <YAxis />
                  <Tooltip />
                  <Line
                    type="monotone"
                    dataKey="total_messages_monitored"
                    stroke="#3b82f6"
                    name="监控消息"
                  />
                  <Line
                    type="monotone"
                    dataKey="keyword_triggered_count"
                    stroke="#10b981"
                    name="关键词触发"
                  />
                </LineChart>
              </ResponsiveContainer>
            </div>
          </CardContent>
        </Card>

        {/* 回复统计图 */}
        <Card>
          <CardHeader>
            <h3 className="text-lg font-semibold">回复统计（近7天）</h3>
          </CardHeader>
          <CardContent>
            <div className="h-64">
              <ResponsiveContainer width="100%" height="100%">
                <BarChart data={recent_stats || []}>
                  <CartesianGrid strokeDasharray="3 3" />
                  <XAxis dataKey="date" />
                  <YAxis />
                  <Tooltip />
                  <Bar dataKey="group_replies_sent" fill="#8b5cf6" name="群内回复" />
                  <Bar dataKey="private_messages_sent" fill="#f59e0b" name="私信发送" />
                </BarChart>
              </ResponsiveContainer>
            </div>
          </CardContent>
        </Card>
      </div>

      {/* 底部信息 */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* 账号状态 */}
        <Card>
          <CardHeader>
            <h3 className="text-lg font-semibold">账号状态</h3>
          </CardHeader>
          <CardContent>
            <div className="grid grid-cols-4 gap-4">
              <div className="text-center p-4 bg-gray-50 rounded-lg">
                <p className="text-2xl font-bold">{account_status?.total || 0}</p>
                <p className="text-sm text-gray-500">总数</p>
              </div>
              <div className="text-center p-4 bg-green-50 rounded-lg">
                <p className="text-2xl font-bold text-green-600">
                  {account_status?.active || 0}
                </p>
                <p className="text-sm text-gray-500">正常</p>
              </div>
              <div className="text-center p-4 bg-yellow-50 rounded-lg">
                <p className="text-2xl font-bold text-yellow-600">
                  {account_status?.limited || 0}
                </p>
                <p className="text-sm text-gray-500">受限</p>
              </div>
              <div className="text-center p-4 bg-red-50 rounded-lg">
                <p className="text-2xl font-bold text-red-600">
                  {account_status?.banned || 0}
                </p>
                <p className="text-sm text-gray-500">封禁</p>
              </div>
            </div>
          </CardContent>
        </Card>

        {/* 最近告警 */}
        <Card>
          <CardHeader>
            <h3 className="text-lg font-semibold">最近告警</h3>
          </CardHeader>
          <CardContent>
            {recent_alerts && recent_alerts.length > 0 ? (
              <div className="space-y-3">
                {recent_alerts.slice(0, 5).map((alert) => (
                  <div
                    key={alert.id}
                    className="flex items-start space-x-3 p-3 bg-gray-50 rounded-lg"
                  >
                    <AlertTriangle
                      className={`w-5 h-5 flex-shrink-0 ${
                        alert.severity === 'error'
                          ? 'text-red-500'
                          : alert.severity === 'warning'
                          ? 'text-yellow-500'
                          : 'text-blue-500'
                      }`}
                    />
                    <div className="flex-1 min-w-0">
                      <p className="text-sm font-medium text-gray-900 truncate">
                        {alert.title}
                      </p>
                      <p className="text-xs text-gray-500">
                        {formatDateTime(alert.created_at)}
                      </p>
                    </div>
                    <Badge
                      variant={
                        alert.severity === 'error'
                          ? 'danger'
                          : alert.severity === 'warning'
                          ? 'warning'
                          : 'info'
                      }
                    >
                      {alert.severity}
                    </Badge>
                  </div>
                ))}
              </div>
            ) : (
              <p className="text-center text-gray-500 py-8">暂无告警</p>
            )}
          </CardContent>
        </Card>
      </div>
    </div>
  );
}
