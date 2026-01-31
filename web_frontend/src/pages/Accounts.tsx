import React, { useState } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { Plus, RefreshCw, Trash2, Heart, LogIn } from 'lucide-react';
import { accountsApi } from '@/services/api';
import { formatDateTime, statusColors, statusTexts } from '@/utils';
import {
  Button,
  Card,
  CardHeader,
  CardContent,
  Badge,
  Table,
  TableHeader,
  TableBody,
  TableRow,
  TableHead,
  TableCell,
  Modal,
  Input,
  Loading,
  Empty,
} from '@/components/ui';
import type { Account } from '@/types';

export default function Accounts() {
  const queryClient = useQueryClient();
  const [showAddModal, setShowAddModal] = useState(false);
  const [showLoginModal, setShowLoginModal] = useState(false);
  const [selectedAccount, setSelectedAccount] = useState<Account | null>(null);
  const [newPhone, setNewPhone] = useState('');
  const [newSessionName, setNewSessionName] = useState('');
  const [loginCode, setLoginCode] = useState('');
  const [loginPassword, setLoginPassword] = useState('');
  const [loginStep, setLoginStep] = useState<'code' | 'password'>('code');

  // 获取账号列表
  const { data, isLoading } = useQuery({
    queryKey: ['accounts'],
    queryFn: accountsApi.getAll,
  });

  // 创建账号
  const createMutation = useMutation({
    mutationFn: accountsApi.create,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['accounts'] });
      setShowAddModal(false);
      setNewPhone('');
      setNewSessionName('');
    },
  });

  // 开始登录
  const startLoginMutation = useMutation({
    mutationFn: (id: number) => accountsApi.startLogin(id),
    onSuccess: (data) => {
      if (data.status === 'authorized') {
        queryClient.invalidateQueries({ queryKey: ['accounts'] });
        setShowLoginModal(false);
      } else {
        setLoginStep('code');
      }
    },
  });

  // 完成登录
  const completeLoginMutation = useMutation({
    mutationFn: ({ id, code, password }: { id: number; code?: string; password?: string }) =>
      accountsApi.completeLogin(id, { code, password }),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['accounts'] });
      setShowLoginModal(false);
      setLoginCode('');
      setLoginPassword('');
    },
    onError: (error: any) => {
      if (error.response?.data?.detail?.includes('password')) {
        setLoginStep('password');
      }
    },
  });

  // 重新连接
  const reconnectMutation = useMutation({
    mutationFn: accountsApi.reconnect,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['accounts'] });
    },
  });

  // 健康检查
  const healthCheckMutation = useMutation({
    mutationFn: accountsApi.checkHealth,
  });

  // 删除账号
  const deleteMutation = useMutation({
    mutationFn: accountsApi.delete,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['accounts'] });
    },
  });

  const handleAddAccount = () => {
    if (!newPhone || !newSessionName) return;
    createMutation.mutate({
      phone_number: newPhone,
      session_name: newSessionName,
    });
  };

  const handleStartLogin = (account: Account) => {
    setSelectedAccount(account);
    setShowLoginModal(true);
    setLoginStep('code');
    startLoginMutation.mutate(account.id);
  };

  const handleCompleteLogin = () => {
    if (!selectedAccount) return;
    if (loginStep === 'code') {
      completeLoginMutation.mutate({ id: selectedAccount.id, code: loginCode });
    } else {
      completeLoginMutation.mutate({ id: selectedAccount.id, password: loginPassword });
    }
  };

  if (isLoading) return <Loading />;

  const accounts = data?.accounts || [];

  return (
    <div className="space-y-6 animate-fadeIn">
      <div className="flex items-center justify-between">
        <h1 className="text-2xl font-bold text-gray-900">账号管理</h1>
        <Button onClick={() => setShowAddModal(true)}>
          <Plus className="w-4 h-4 mr-2" />
          添加账号
        </Button>
      </div>

      <Card>
        <CardHeader>
          <p className="text-sm text-gray-500">
            管理 Telegram 账号，用于消息监听和自动回复。建议使用多个小号轮换发送消息。
          </p>
        </CardHeader>
        <CardContent className="p-0">
          {accounts.length === 0 ? (
            <Empty message="暂无账号，请添加" />
          ) : (
            <Table>
              <TableHeader>
                <TableRow>
                  <TableHead>手机号</TableHead>
                  <TableHead>Session 名称</TableHead>
                  <TableHead>状态</TableHead>
                  <TableHead>今日发送</TableHead>
                  <TableHead>最后使用</TableHead>
                  <TableHead>操作</TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {accounts.map((account) => (
                  <TableRow key={account.id}>
                    <TableCell className="font-medium">{account.phone_number}</TableCell>
                    <TableCell>{account.session_name}</TableCell>
                    <TableCell>
                      <Badge
                        className={statusColors[account.status] || 'bg-gray-100 text-gray-800'}
                      >
                        {statusTexts[account.status] || account.status}
                      </Badge>
                    </TableCell>
                    <TableCell>{account.daily_message_count}</TableCell>
                    <TableCell>
                      {account.last_used_at ? formatDateTime(account.last_used_at) : '-'}
                    </TableCell>
                    <TableCell>
                      <div className="flex items-center space-x-2">
                        {account.status === 'logging_in' || account.status === 'need_password' ? (
                          <Button
                            size="sm"
                            variant="primary"
                            onClick={() => handleStartLogin(account)}
                          >
                            <LogIn className="w-4 h-4" />
                          </Button>
                        ) : (
                          <>
                            <Button
                              size="sm"
                              variant="ghost"
                              onClick={() => reconnectMutation.mutate(account.id)}
                              loading={reconnectMutation.isPending}
                            >
                              <RefreshCw className="w-4 h-4" />
                            </Button>
                            <Button
                              size="sm"
                              variant="ghost"
                              onClick={() => healthCheckMutation.mutate(account.id)}
                            >
                              <Heart className="w-4 h-4" />
                            </Button>
                          </>
                        )}
                        <Button
                          size="sm"
                          variant="ghost"
                          onClick={() => {
                            if (confirm('确定要删除此账号吗？')) {
                              deleteMutation.mutate(account.id);
                            }
                          }}
                        >
                          <Trash2 className="w-4 h-4 text-red-500" />
                        </Button>
                      </div>
                    </TableCell>
                  </TableRow>
                ))}
              </TableBody>
            </Table>
          )}
        </CardContent>
      </Card>

      {/* 添加账号模态框 */}
      <Modal
        isOpen={showAddModal}
        onClose={() => setShowAddModal(false)}
        title="添加账号"
      >
        <div className="space-y-4">
          <Input
            label="手机号"
            placeholder="例如: +992901234567"
            value={newPhone}
            onChange={(e) => setNewPhone(e.target.value)}
          />
          <Input
            label="Session 名称"
            placeholder="例如: account_1"
            value={newSessionName}
            onChange={(e) => setNewSessionName(e.target.value)}
          />
          <div className="flex justify-end space-x-3 mt-6">
            <Button variant="secondary" onClick={() => setShowAddModal(false)}>
              取消
            </Button>
            <Button onClick={handleAddAccount} loading={createMutation.isPending}>
              添加
            </Button>
          </div>
        </div>
      </Modal>

      {/* 登录模态框 */}
      <Modal
        isOpen={showLoginModal}
        onClose={() => setShowLoginModal(false)}
        title={`登录账号: ${selectedAccount?.phone_number}`}
      >
        <div className="space-y-4">
          {startLoginMutation.isPending ? (
            <div className="text-center py-4">
              <Loading />
              <p className="text-sm text-gray-500 mt-2">正在发送验证码...</p>
            </div>
          ) : loginStep === 'code' ? (
            <Input
              label="验证码"
              placeholder="请输入收到的验证码"
              value={loginCode}
              onChange={(e) => setLoginCode(e.target.value)}
            />
          ) : (
            <Input
              label="两步验证密码"
              type="password"
              placeholder="请输入两步验证密码"
              value={loginPassword}
              onChange={(e) => setLoginPassword(e.target.value)}
            />
          )}
          <div className="flex justify-end space-x-3 mt-6">
            <Button variant="secondary" onClick={() => setShowLoginModal(false)}>
              取消
            </Button>
            <Button
              onClick={handleCompleteLogin}
              loading={completeLoginMutation.isPending}
              disabled={startLoginMutation.isPending}
            >
              确认
            </Button>
          </div>
        </div>
      </Modal>
    </div>
  );
}
