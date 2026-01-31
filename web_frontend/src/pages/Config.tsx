import React, { useState, useEffect } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { Save, TestTube } from 'lucide-react';
import { configApi, dashboardApi } from '@/services/api';
import {
  Button,
  Card,
  CardHeader,
  CardContent,
  CardFooter,
  Input,
  Switch,
  Loading,
} from '@/components/ui';

interface ConfigFormData {
  // Dify 配置
  dify_api_url: string;
  dify_api_key: string;
  dify_workflow_id: string;
  dify_knowledge_workflow_id: string;
  dify_confidence_threshold: number;
  
  // 防风控配置
  private_message_interval_minutes: number;
  user_cooldown_days: number;
  daily_private_message_limit: number;
  hourly_group_reply_limit: number;
  
  // 延迟配置
  reply_delay_min_seconds: number;
  reply_delay_max_seconds: number;
  typing_duration_min_seconds: number;
  typing_duration_max_seconds: number;
  
  // 活跃时段
  active_hours_start: number;
  active_hours_end: number;
  
  // 功能开关
  enable_group_reply: boolean;
  enable_private_message: boolean;
  enable_dify_analysis: boolean;
  
  // 回复模板
  group_reply_template: string;
  private_reply_template: string;
}

const defaultConfig: ConfigFormData = {
  dify_api_url: 'http://localhost/v1',
  dify_api_key: '',
  dify_workflow_id: '',
  dify_knowledge_workflow_id: '',
  dify_confidence_threshold: 0.7,
  private_message_interval_minutes: 5,
  user_cooldown_days: 3,
  daily_private_message_limit: 20,
  hourly_group_reply_limit: 3,
  reply_delay_min_seconds: 10,
  reply_delay_max_seconds: 60,
  typing_duration_min_seconds: 2,
  typing_duration_max_seconds: 5,
  active_hours_start: 8,
  active_hours_end: 24,
  enable_group_reply: true,
  enable_private_message: true,
  enable_dify_analysis: true,
  group_reply_template: '您好 {username}！感谢您的咨询，我们的专业顾问会尽快与您联系。',
  private_reply_template: '您好！感谢您对我们服务的关注。我是 Tezbarakat 的客服，很高兴为您服务。请问有什么可以帮助您的？',
};

export default function Config() {
  const queryClient = useQueryClient();
  const [formData, setFormData] = useState<ConfigFormData>(defaultConfig);
  const [testResult, setTestResult] = useState<{ success: boolean; message: string } | null>(null);

  // 获取配置
  const { data, isLoading } = useQuery({
    queryKey: ['config'],
    queryFn: configApi.getAll,
  });

  // 更新配置
  const updateMutation = useMutation({
    mutationFn: configApi.batchUpdate,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['config'] });
      alert('配置保存成功！');
    },
  });

  // 测试 Dify 连接
  const testDifyMutation = useMutation({
    mutationFn: dashboardApi.testDify,
    onSuccess: (result) => {
      setTestResult({ success: result.success, message: result.message || '' });
    },
  });

  // 加载配置到表单
  useEffect(() => {
    if (data?.configs) {
      const configMap: Record<string, any> = {};
      data.configs.forEach((c) => {
        // 处理 JSONB 值
        let value = c.value;
        if (typeof value === 'string') {
          // 尝试解析 JSON 字符串
          try {
            value = JSON.parse(value);
          } catch {
            // 保持原值
          }
        }
        configMap[c.key] = value;
      });
      setFormData((prev) => ({
        ...prev,
        ...configMap,
      }));
    }
  }, [data]);

  const handleChange = (key: keyof ConfigFormData, value: any) => {
    setFormData((prev) => ({
      ...prev,
      [key]: value,
    }));
  };

  const handleSave = () => {
    updateMutation.mutate(formData);
  };

  if (isLoading) return <Loading />;

  return (
    <div className="space-y-6 animate-fadeIn">
      <div className="flex items-center justify-between">
        <h1 className="text-2xl font-bold text-gray-900">系统配置</h1>
        <Button onClick={handleSave} loading={updateMutation.isPending}>
          <Save className="w-4 h-4 mr-2" />
          保存配置
        </Button>
      </div>

      {/* Dify 配置 */}
      <Card>
        <CardHeader>
          <h3 className="text-lg font-semibold">Dify AI 配置</h3>
          <p className="text-sm text-gray-500">配置 Dify 自部署服务的连接信息</p>
        </CardHeader>
        <CardContent className="space-y-4">
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <Input
              label="Dify API 地址"
              value={formData.dify_api_url}
              onChange={(e) => handleChange('dify_api_url', e.target.value)}
              placeholder="http://localhost/v1"
            />
            <Input
              label="Dify API 密钥"
              type="password"
              value={formData.dify_api_key}
              onChange={(e) => handleChange('dify_api_key', e.target.value)}
              placeholder="app-xxxxxxxx"
            />
            <Input
              label="意图分析工作流 ID"
              value={formData.dify_workflow_id}
              onChange={(e) => handleChange('dify_workflow_id', e.target.value)}
              placeholder="工作流 ID"
            />
            <Input
              label="知识库对话工作流 ID"
              value={formData.dify_knowledge_workflow_id}
              onChange={(e) => handleChange('dify_knowledge_workflow_id', e.target.value)}
              placeholder="工作流 ID"
            />
            <Input
              label="置信度阈值"
              type="number"
              min={0}
              max={1}
              step={0.1}
              value={formData.dify_confidence_threshold}
              onChange={(e) => handleChange('dify_confidence_threshold', parseFloat(e.target.value))}
            />
          </div>
        </CardContent>
        <CardFooter>
          <div className="flex items-center space-x-4">
            <Button
              variant="secondary"
              onClick={() => testDifyMutation.mutate()}
              loading={testDifyMutation.isPending}
            >
              <TestTube className="w-4 h-4 mr-2" />
              测试连接
            </Button>
            {testResult && (
              <span className={testResult.success ? 'text-green-600' : 'text-red-600'}>
                {testResult.message}
              </span>
            )}
          </div>
        </CardFooter>
      </Card>

      {/* 防风控配置 */}
      <Card>
        <CardHeader>
          <h3 className="text-lg font-semibold">防风控配置</h3>
          <p className="text-sm text-gray-500">配置消息发送频率限制，防止账号被封禁</p>
        </CardHeader>
        <CardContent>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <Input
              label="私信间隔（分钟）"
              type="number"
              min={1}
              value={formData.private_message_interval_minutes}
              onChange={(e) => handleChange('private_message_interval_minutes', parseInt(e.target.value))}
            />
            <Input
              label="用户冷却期（天）"
              type="number"
              min={1}
              value={formData.user_cooldown_days}
              onChange={(e) => handleChange('user_cooldown_days', parseInt(e.target.value))}
            />
            <Input
              label="每日私信上限"
              type="number"
              min={1}
              value={formData.daily_private_message_limit}
              onChange={(e) => handleChange('daily_private_message_limit', parseInt(e.target.value))}
            />
            <Input
              label="每小时群回复上限"
              type="number"
              min={1}
              value={formData.hourly_group_reply_limit}
              onChange={(e) => handleChange('hourly_group_reply_limit', parseInt(e.target.value))}
            />
          </div>
        </CardContent>
      </Card>

      {/* 延迟配置 */}
      <Card>
        <CardHeader>
          <h3 className="text-lg font-semibold">回复延迟配置</h3>
          <p className="text-sm text-gray-500">配置回复延迟，模拟真人行为</p>
        </CardHeader>
        <CardContent>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <Input
              label="回复延迟最小（秒）"
              type="number"
              min={0}
              value={formData.reply_delay_min_seconds}
              onChange={(e) => handleChange('reply_delay_min_seconds', parseInt(e.target.value))}
            />
            <Input
              label="回复延迟最大（秒）"
              type="number"
              min={0}
              value={formData.reply_delay_max_seconds}
              onChange={(e) => handleChange('reply_delay_max_seconds', parseInt(e.target.value))}
            />
            <Input
              label="打字状态最小（秒）"
              type="number"
              min={0}
              value={formData.typing_duration_min_seconds}
              onChange={(e) => handleChange('typing_duration_min_seconds', parseInt(e.target.value))}
            />
            <Input
              label="打字状态最大（秒）"
              type="number"
              min={0}
              value={formData.typing_duration_max_seconds}
              onChange={(e) => handleChange('typing_duration_max_seconds', parseInt(e.target.value))}
            />
          </div>
        </CardContent>
      </Card>

      {/* 活跃时段配置 */}
      <Card>
        <CardHeader>
          <h3 className="text-lg font-semibold">活跃时段配置</h3>
          <p className="text-sm text-gray-500">配置 Bot 的活跃时间段（塔吉克斯坦时间）</p>
        </CardHeader>
        <CardContent>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <Input
              label="开始时间（小时）"
              type="number"
              min={0}
              max={23}
              value={formData.active_hours_start}
              onChange={(e) => handleChange('active_hours_start', parseInt(e.target.value))}
            />
            <Input
              label="结束时间（小时）"
              type="number"
              min={1}
              max={24}
              value={formData.active_hours_end}
              onChange={(e) => handleChange('active_hours_end', parseInt(e.target.value))}
            />
          </div>
        </CardContent>
      </Card>

      {/* 回复模板配置 */}
      <Card>
        <CardHeader>
          <h3 className="text-lg font-semibold">回复模板配置</h3>
          <p className="text-sm text-gray-500">配置禁用 Dify 时使用的回复模板，支持变量：{'{username}'}, {'{name}'}, {'{first_name}'}</p>
        </CardHeader>
        <CardContent>
          <div className="space-y-4">
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                群内回复模板
              </label>
              <textarea
                className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
                rows={3}
                value={formData.group_reply_template}
                onChange={(e) => handleChange('group_reply_template', e.target.value)}
                placeholder="您好 {username}！感谢您的咨询..."
              />
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                私信回复模板
              </label>
              <textarea
                className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
                rows={3}
                value={formData.private_reply_template}
                onChange={(e) => handleChange('private_reply_template', e.target.value)}
                placeholder="您好！感谢您对我们服务的关注..."
              />
            </div>
          </div>
        </CardContent>
      </Card>

      {/* 功能开关 */}
      <Card>
        <CardHeader>
          <h3 className="text-lg font-semibold">功能开关</h3>
          <p className="text-sm text-gray-500">启用或禁用特定功能</p>
        </CardHeader>
        <CardContent>
          <div className="space-y-4">
            <div className="flex items-center justify-between">
              <div>
                <p className="font-medium">Dify AI 分析</p>
                <p className="text-sm text-gray-500">启用后，使用 Dify 进行意图分析；禁用后，使用模板回复</p>
              </div>
              <Switch
                checked={formData.enable_dify_analysis}
                onChange={(checked) => handleChange('enable_dify_analysis', checked)}
              />
            </div>
            <div className="flex items-center justify-between">
              <div>
                <p className="font-medium">群内回复</p>
                <p className="text-sm text-gray-500">启用后，Bot 会在群内 @用户 回复</p>
              </div>
              <Switch
                checked={formData.enable_group_reply}
                onChange={(checked) => handleChange('enable_group_reply', checked)}
              />
            </div>
            <div className="flex items-center justify-between">
              <div>
                <p className="font-medium">私信功能</p>
                <p className="text-sm text-gray-500">启用后，Bot 会向用户发送私信</p>
              </div>
              <Switch
                checked={formData.enable_private_message}
                onChange={(checked) => handleChange('enable_private_message', checked)}
              />
            </div>
          </div>
        </CardContent>
      </Card>
    </div>
  );
}
