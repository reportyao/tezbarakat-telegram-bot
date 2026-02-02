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
  TrendingUp,
  Target,
  Link,
  MessageCircle,
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
  Legend,
  AreaChart,
  Area,
} from 'recharts';
import { dashboardApi, ConversionStats } from '@/services/api';
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

  // 获取转化率统计数据
  const { data: conversionData } = useQuery({
    queryKey: ['conversion-stats'],
    queryFn: () => dashboardApi.getConversionStats(7),
    refetchInterval: 60000, // 每60秒刷新
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

  // 转化率统计卡片
  const conversionCards = conversionData ? [
    {
      title: '开始对话',
      value: conversionData.summary.total_conversations,
      icon: MessageCircle,
      color: 'text-blue-600',
      bgColor: 'bg-blue-100',
    },
    {
      title: '用户回复',
      value: conversionData.summary.total_user_replies,
      subValue: `回复率 ${(conversionData.summary.reply_rate * 100).toFixed(1)}%`,
      icon: Users,
      color: 'text-green-600',
      bgColor: 'bg-green-100',
    },
    {
      title: '完成转化',
      value: conversionData.summary.total_completed,
      subValue: `转化率 ${(conversionData.summary.conversion_rate * 100).toFixed(1)}%`,
      icon: Target,
      color: 'text-purple-600',
      bgColor: 'bg-purple-100',
    },
    {
      title: '发送链接',
      value: conversionData.summary.total_links_provided,
      subValue: `链接率 ${(conversionData.summary.link_conversion_rate * 100).toFixed(1)}%`,
      icon: Link,
      color: 'text-orange-600',
      bgColor: 'bg-orange-100',
    },
  ] : [];

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

      {/* 转化率统计区域 */}
      {conversionData && (
        <>
          <div className="flex items-center space-x-2 mt-8">
            <TrendingUp className="w-5 h-5 text-green-600" />
            <h2 className="text-xl font-bold text-gray-900">转化率统计（近7天）</h2>
          </div>

          {/* 转化率统计卡片 */}
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
            {conversionCards.map((stat) => (
              <Card key={stat.title}>
                <CardContent className="py-4">
                  <div className="flex items-center justify-between">
                    <div>
                      <p className="text-sm text-gray-500">{stat.title}</p>
                      <p className="text-2xl font-bold mt-1">{formatNumber(stat.value)}</p>
                      {stat.subValue && (
                        <p className="text-sm text-green-600 mt-1">{stat.subValue}</p>
                      )}
                    </div>
                    <div className={`p-3 rounded-full ${stat.bgColor}`}>
                      <stat.icon className={`w-6 h-6 ${stat.color}`} />
                    </div>
                  </div>
                </CardContent>
              </Card>
            ))}
          </div>

          {/* 对话阶段漏斗 */}
          <Card>
            <CardHeader>
              <h3 className="text-lg font-semibold">对话阶段漏斗</h3>
            </CardHeader>
            <CardContent>
              <div className="grid grid-cols-5 gap-4">
                {[
                  { stage: 1, label: '破冰共情', value: conversionData.stage_stats.stage_1, color: 'bg-blue-500' },
                  { stage: 2, label: '埋下钩子', value: conversionData.stage_stats.stage_2, color: 'bg-green-500' },
                  { stage: 3, label: '揭示平台', value: conversionData.stage_stats.stage_3, color: 'bg-yellow-500' },
                  { stage: 4, label: '简述价值', value: conversionData.stage_stats.stage_4, color: 'bg-orange-500' },
                  { stage: 5, label: '提供链接', value: conversionData.stage_stats.stage_5, color: 'bg-purple-500' },
                ].map((item) => (
                  <div key={item.stage} className="text-center">
                    <div className={`${item.color} text-white rounded-lg p-4 mb-2`}>
                      <p className="text-2xl font-bold">{item.value}</p>
                    </div>
                    <p className="text-sm font-medium text-gray-700">Stage {item.stage}</p>
                    <p className="text-xs text-gray-500">{item.label}</p>
                  </div>
                ))}
              </div>
            </CardContent>
          </Card>

          {/* 转化率趋势图 */}
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
            <Card>
              <CardHeader>
                <h3 className="text-lg font-semibold">对话与转化趋势</h3>
              </CardHeader>
              <CardContent>
                <div className="h-64">
                  <ResponsiveContainer width="100%" height="100%">
                    <AreaChart data={conversionData.daily_stats}>
                      <CartesianGrid strokeDasharray="3 3" />
                      <XAxis dataKey="date" />
                      <YAxis />
                      <Tooltip />
                      <Legend />
                      <Area
                        type="monotone"
                        dataKey="conversations_started"
                        stackId="1"
                        stroke="#3b82f6"
                        fill="#93c5fd"
                        name="开始对话"
                      />
                      <Area
                        type="monotone"
                        dataKey="user_replies_received"
                        stackId="2"
                        stroke="#10b981"
                        fill="#6ee7b7"
                        name="用户回复"
                      />
                      <Area
                        type="monotone"
                        dataKey="conversations_completed"
                        stackId="3"
                        stroke="#8b5cf6"
                        fill="#c4b5fd"
                        name="完成转化"
                      />
                    </AreaChart>
                  </ResponsiveContainer>
                </div>
              </CardContent>
            </Card>

            <Card>
              <CardHeader>
                <h3 className="text-lg font-semibold">转化率趋势</h3>
              </CardHeader>
              <CardContent>
                <div className="h-64">
                  <ResponsiveContainer width="100%" height="100%">
                    <LineChart data={conversionData.daily_stats}>
                      <CartesianGrid strokeDasharray="3 3" />
                      <XAxis dataKey="date" />
                      <YAxis tickFormatter={(value) => `${(value * 100).toFixed(0)}%`} />
                      <Tooltip formatter={(value: number) => `${(value * 100).toFixed(1)}%`} />
                      <Legend />
                      <Line
                        type="monotone"
                        dataKey="reply_rate"
                        stroke="#10b981"
                        strokeWidth={2}
                        name="回复率"
                      />
                      <Line
                        type="monotone"
                        dataKey="conversion_rate"
                        stroke="#8b5cf6"
                        strokeWidth={2}
                        name="转化率"
                      />
                    </LineChart>
                  </ResponsiveContainer>
                </div>
              </CardContent>
            </Card>
          </div>
        </>
      )}

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
