import React, { useState } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { Plus, Trash2, Search, ExternalLink } from 'lucide-react';
import { groupsApi } from '@/services/api';
import { formatDateTime } from '@/utils';
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
  Switch,
  Loading,
  Empty,
} from '@/components/ui';
import type { Group } from '@/types';

export default function Groups() {
  const queryClient = useQueryClient();
  const [showAddModal, setShowAddModal] = useState(false);
  const [groupUsername, setGroupUsername] = useState('');
  const [resolvedGroup, setResolvedGroup] = useState<{
    group_id: number;
    title: string;
    username?: string;
  } | null>(null);

  // 获取群组列表
  const { data, isLoading } = useQuery({
    queryKey: ['groups'],
    queryFn: groupsApi.getAll,
  });

  // 解析群组
  const resolveMutation = useMutation({
    mutationFn: groupsApi.resolve,
    onSuccess: (data) => {
      setResolvedGroup(data);
    },
  });

  // 创建群组
  const createMutation = useMutation({
    mutationFn: groupsApi.create,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['groups'] });
      setShowAddModal(false);
      setGroupUsername('');
      setResolvedGroup(null);
    },
  });

  // 更新群组
  const updateMutation = useMutation({
    mutationFn: ({ id, data }: { id: number; data: { is_active?: boolean } }) =>
      groupsApi.update(id, data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['groups'] });
    },
  });

  // 删除群组
  const deleteMutation = useMutation({
    mutationFn: groupsApi.delete,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['groups'] });
    },
  });

  const handleResolve = () => {
    if (!groupUsername) return;
    resolveMutation.mutate(groupUsername);
  };

  const handleAddGroup = () => {
    if (!resolvedGroup) return;
    createMutation.mutate({
      group_id: resolvedGroup.group_id,
      group_name: resolvedGroup.title,
      username: resolvedGroup.username,
    });
  };

  if (isLoading) return <Loading />;

  const groups = data?.groups || [];

  return (
    <div className="space-y-6 animate-fadeIn">
      <div className="flex items-center justify-between">
        <h1 className="text-2xl font-bold text-gray-900">群组管理</h1>
        <Button onClick={() => setShowAddModal(true)}>
          <Plus className="w-4 h-4 mr-2" />
          添加群组
        </Button>
      </div>

      <Card>
        <CardHeader>
          <p className="text-sm text-gray-500">
            管理需要监听的 Telegram 群组。Bot 会监听这些群组中的消息并根据关键词触发回复。
          </p>
        </CardHeader>
        <CardContent className="p-0">
          {groups.length === 0 ? (
            <Empty message="暂无群组，请添加" />
          ) : (
            <Table>
              <TableHeader>
                <TableRow>
                  <TableHead>群组名称</TableHead>
                  <TableHead>用户名</TableHead>
                  <TableHead>群组 ID</TableHead>
                  <TableHead>小时回复数</TableHead>
                  <TableHead>状态</TableHead>
                  <TableHead>添加时间</TableHead>
                  <TableHead>操作</TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {groups.map((group) => (
                  <TableRow key={group.id}>
                    <TableCell className="font-medium">{group.group_name}</TableCell>
                    <TableCell>
                      {group.username ? (
                        <a
                          href={`https://t.me/${group.username}`}
                          target="_blank"
                          rel="noopener noreferrer"
                          className="text-primary-600 hover:underline flex items-center"
                        >
                          @{group.username}
                          <ExternalLink className="w-3 h-3 ml-1" />
                        </a>
                      ) : (
                        '-'
                      )}
                    </TableCell>
                    <TableCell className="font-mono text-sm">{group.group_id}</TableCell>
                    <TableCell>{group.hourly_reply_count}</TableCell>
                    <TableCell>
                      <Switch
                        checked={group.is_active}
                        onChange={(checked) =>
                          updateMutation.mutate({ id: group.id, data: { is_active: checked } })
                        }
                      />
                    </TableCell>
                    <TableCell>{formatDateTime(group.created_at)}</TableCell>
                    <TableCell>
                      <Button
                        size="sm"
                        variant="ghost"
                        onClick={() => {
                          if (confirm('确定要删除此群组吗？')) {
                            deleteMutation.mutate(group.id);
                          }
                        }}
                      >
                        <Trash2 className="w-4 h-4 text-red-500" />
                      </Button>
                    </TableCell>
                  </TableRow>
                ))}
              </TableBody>
            </Table>
          )}
        </CardContent>
      </Card>

      {/* 添加群组模态框 */}
      <Modal
        isOpen={showAddModal}
        onClose={() => {
          setShowAddModal(false);
          setGroupUsername('');
          setResolvedGroup(null);
        }}
        title="添加群组"
      >
        <div className="space-y-4">
          <div className="flex space-x-2">
            <Input
              placeholder="输入群组用户名，例如: tezbarakat_chat"
              value={groupUsername}
              onChange={(e) => setGroupUsername(e.target.value)}
              className="flex-1"
            />
            <Button onClick={handleResolve} loading={resolveMutation.isPending}>
              <Search className="w-4 h-4" />
            </Button>
          </div>

          {resolvedGroup && (
            <div className="p-4 bg-gray-50 rounded-lg">
              <p className="font-medium">{resolvedGroup.title}</p>
              <p className="text-sm text-gray-500">
                ID: {resolvedGroup.group_id}
                {resolvedGroup.username && ` | @${resolvedGroup.username}`}
              </p>
            </div>
          )}

          <div className="flex justify-end space-x-3 mt-6">
            <Button
              variant="secondary"
              onClick={() => {
                setShowAddModal(false);
                setGroupUsername('');
                setResolvedGroup(null);
              }}
            >
              取消
            </Button>
            <Button
              onClick={handleAddGroup}
              loading={createMutation.isPending}
              disabled={!resolvedGroup}
            >
              添加
            </Button>
          </div>
        </div>
      </Modal>
    </div>
  );
}
