import React, { useState } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { Plus, Trash2, Upload } from 'lucide-react';
import { keywordsApi } from '@/services/api';
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

export default function Keywords() {
  const queryClient = useQueryClient();
  const [showAddModal, setShowAddModal] = useState(false);
  const [showBatchModal, setShowBatchModal] = useState(false);
  const [newKeyword, setNewKeyword] = useState('');
  const [batchKeywords, setBatchKeywords] = useState('');

  // 获取关键词列表
  const { data, isLoading } = useQuery({
    queryKey: ['keywords'],
    queryFn: keywordsApi.getAll,
  });

  // 创建关键词
  const createMutation = useMutation({
    mutationFn: keywordsApi.create,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['keywords'] });
      setShowAddModal(false);
      setNewKeyword('');
    },
  });

  // 批量创建
  const batchCreateMutation = useMutation({
    mutationFn: keywordsApi.batchCreate,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['keywords'] });
      setShowBatchModal(false);
      setBatchKeywords('');
    },
  });

  // 更新关键词
  const updateMutation = useMutation({
    mutationFn: ({ id, data }: { id: number; data: { is_active?: boolean } }) =>
      keywordsApi.update(id, data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['keywords'] });
    },
  });

  // 删除关键词
  const deleteMutation = useMutation({
    mutationFn: keywordsApi.delete,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['keywords'] });
    },
  });

  const handleAddKeyword = () => {
    if (!newKeyword.trim()) return;
    createMutation.mutate({ keyword: newKeyword.trim() });
  };

  const handleBatchCreate = () => {
    const keywords = batchKeywords
      .split('\n')
      .map((k) => k.trim())
      .filter((k) => k.length > 0);
    if (keywords.length === 0) return;
    batchCreateMutation.mutate(keywords);
  };

  if (isLoading) return <Loading />;

  const keywords = data?.keywords || [];

  // 统计
  const activeCount = keywords.filter((k) => k.is_active).length;
  const totalHits = keywords.reduce((sum, k) => sum + k.hit_count, 0);

  return (
    <div className="space-y-6 animate-fadeIn">
      <div className="flex items-center justify-between">
        <h1 className="text-2xl font-bold text-gray-900">关键词管理</h1>
        <div className="flex space-x-2">
          <Button variant="secondary" onClick={() => setShowBatchModal(true)}>
            <Upload className="w-4 h-4 mr-2" />
            批量导入
          </Button>
          <Button onClick={() => setShowAddModal(true)}>
            <Plus className="w-4 h-4 mr-2" />
            添加关键词
          </Button>
        </div>
      </div>

      {/* 统计卡片 */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
        <Card>
          <CardContent className="py-4">
            <p className="text-sm text-gray-500">总关键词数</p>
            <p className="text-2xl font-bold">{keywords.length}</p>
          </CardContent>
        </Card>
        <Card>
          <CardContent className="py-4">
            <p className="text-sm text-gray-500">启用中</p>
            <p className="text-2xl font-bold text-green-600">{activeCount}</p>
          </CardContent>
        </Card>
        <Card>
          <CardContent className="py-4">
            <p className="text-sm text-gray-500">总命中次数</p>
            <p className="text-2xl font-bold text-blue-600">{totalHits}</p>
          </CardContent>
        </Card>
      </div>

      <Card>
        <CardHeader>
          <p className="text-sm text-gray-500">
            配置触发自动回复的关键词。支持塔吉克语、俄语等多语言关键词。
          </p>
        </CardHeader>
        <CardContent className="p-0">
          {keywords.length === 0 ? (
            <Empty message="暂无关键词，请添加" />
          ) : (
            <Table>
              <TableHeader>
                <TableRow>
                  <TableHead>关键词</TableHead>
                  <TableHead>命中次数</TableHead>
                  <TableHead>状态</TableHead>
                  <TableHead>添加时间</TableHead>
                  <TableHead>操作</TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {keywords.map((keyword) => (
                  <TableRow key={keyword.id}>
                    <TableCell className="font-medium">{keyword.keyword}</TableCell>
                    <TableCell>
                      <Badge variant="info">{keyword.hit_count}</Badge>
                    </TableCell>
                    <TableCell>
                      <Switch
                        checked={keyword.is_active}
                        onChange={(checked) =>
                          updateMutation.mutate({
                            id: keyword.id,
                            data: { is_active: checked },
                          })
                        }
                      />
                    </TableCell>
                    <TableCell>{formatDateTime(keyword.created_at)}</TableCell>
                    <TableCell>
                      <Button
                        size="sm"
                        variant="ghost"
                        onClick={() => {
                          if (confirm('确定要删除此关键词吗？')) {
                            deleteMutation.mutate(keyword.id);
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

      {/* 添加关键词模态框 */}
      <Modal
        isOpen={showAddModal}
        onClose={() => setShowAddModal(false)}
        title="添加关键词"
      >
        <div className="space-y-4">
          <Input
            label="关键词"
            placeholder="输入关键词"
            value={newKeyword}
            onChange={(e) => setNewKeyword(e.target.value)}
          />
          <div className="flex justify-end space-x-3 mt-6">
            <Button variant="secondary" onClick={() => setShowAddModal(false)}>
              取消
            </Button>
            <Button onClick={handleAddKeyword} loading={createMutation.isPending}>
              添加
            </Button>
          </div>
        </div>
      </Modal>

      {/* 批量导入模态框 */}
      <Modal
        isOpen={showBatchModal}
        onClose={() => setShowBatchModal(false)}
        title="批量导入关键词"
      >
        <div className="space-y-4">
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">
              关键词列表（每行一个）
            </label>
            <textarea
              className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-primary-500"
              rows={10}
              placeholder="кредит&#10;займ&#10;пул&#10;қарз"
              value={batchKeywords}
              onChange={(e) => setBatchKeywords(e.target.value)}
            />
          </div>
          <div className="flex justify-end space-x-3 mt-6">
            <Button variant="secondary" onClick={() => setShowBatchModal(false)}>
              取消
            </Button>
            <Button onClick={handleBatchCreate} loading={batchCreateMutation.isPending}>
              导入
            </Button>
          </div>
        </div>
      </Modal>
    </div>
  );
}
