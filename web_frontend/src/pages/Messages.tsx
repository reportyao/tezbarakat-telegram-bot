import React, { useState } from 'react';
import { useQuery } from '@tanstack/react-query';
import { MessageSquare, Send, Filter } from 'lucide-react';
import { messagesApi } from '@/services/api';
import { formatDateTime, truncateText } from '@/utils';
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
  Loading,
  Empty,
} from '@/components/ui';

type TabType = 'messages' | 'replies';

export default function Messages() {
  const [activeTab, setActiveTab] = useState<TabType>('messages');
  const [page, setPage] = useState(1);
  const [triggeredOnly, setTriggeredOnly] = useState(false);
  const [replyType, setReplyType] = useState<'all' | 'group' | 'private'>('all');
  const pageSize = 20;

  // 获取消息列表
  const messagesQuery = useQuery({
    queryKey: ['messages', page, triggeredOnly],
    queryFn: () =>
      messagesApi.getMessages({
        page,
        page_size: pageSize,
        triggered_only: triggeredOnly,
      }),
    enabled: activeTab === 'messages',
  });

  // 获取回复列表
  const repliesQuery = useQuery({
    queryKey: ['replies', page, replyType],
    queryFn: () =>
      messagesApi.getReplies({
        page,
        page_size: pageSize,
        reply_type: replyType === 'all' ? undefined : replyType,
      }),
    enabled: activeTab === 'replies',
  });

  const handleTabChange = (tab: TabType) => {
    setActiveTab(tab);
    setPage(1);
  };

  return (
    <div className="space-y-6 animate-fadeIn">
      <div className="flex items-center justify-between">
        <h1 className="text-2xl font-bold text-gray-900">消息记录</h1>
      </div>

      {/* 标签页 */}
      <div className="flex space-x-4 border-b">
        <button
          className={`pb-3 px-1 font-medium transition-colors ${
            activeTab === 'messages'
              ? 'text-primary-600 border-b-2 border-primary-600'
              : 'text-gray-500 hover:text-gray-700'
          }`}
          onClick={() => handleTabChange('messages')}
        >
          <MessageSquare className="w-4 h-4 inline mr-2" />
          监控消息
        </button>
        <button
          className={`pb-3 px-1 font-medium transition-colors ${
            activeTab === 'replies'
              ? 'text-primary-600 border-b-2 border-primary-600'
              : 'text-gray-500 hover:text-gray-700'
          }`}
          onClick={() => handleTabChange('replies')}
        >
          <Send className="w-4 h-4 inline mr-2" />
          发送记录
        </button>
      </div>

      {/* 消息列表 */}
      {activeTab === 'messages' && (
        <Card>
          <CardHeader>
            <div className="flex items-center justify-between">
              <p className="text-sm text-gray-500">
                显示所有监控到的群组消息
              </p>
              <div className="flex items-center space-x-2">
                <Filter className="w-4 h-4 text-gray-400" />
                <label className="flex items-center space-x-2 text-sm">
                  <input
                    type="checkbox"
                    checked={triggeredOnly}
                    onChange={(e) => {
                      setTriggeredOnly(e.target.checked);
                      setPage(1);
                    }}
                    className="rounded border-gray-300 text-primary-600 focus:ring-primary-500"
                  />
                  <span>仅显示触发的消息</span>
                </label>
              </div>
            </div>
          </CardHeader>
          <CardContent className="p-0">
            {messagesQuery.isLoading ? (
              <Loading />
            ) : messagesQuery.data?.messages.length === 0 ? (
              <Empty message="暂无消息记录" />
            ) : (
              <>
                <Table>
                  <TableHeader>
                    <TableRow>
                      <TableHead>时间</TableHead>
                      <TableHead>用户 ID</TableHead>
                      <TableHead>消息内容</TableHead>
                      <TableHead>触发关键词</TableHead>
                      <TableHead>Dify 分析</TableHead>
                    </TableRow>
                  </TableHeader>
                  <TableBody>
                    {messagesQuery.data?.messages.map((message) => (
                      <TableRow key={message.id}>
                        <TableCell className="whitespace-nowrap">
                          {formatDateTime(message.timestamp)}
                        </TableCell>
                        <TableCell className="font-mono text-sm">
                          {message.user_id}
                        </TableCell>
                        <TableCell className="max-w-md">
                          <p className="truncate" title={message.text}>
                            {truncateText(message.text, 100)}
                          </p>
                        </TableCell>
                        <TableCell>
                          {message.triggered_keyword ? (
                            <Badge variant="success">{message.matched_keyword}</Badge>
                          ) : (
                            <span className="text-gray-400">-</span>
                          )}
                        </TableCell>
                        <TableCell>
                          {message.triggered_dify ? (
                            <Badge variant="info">
                              {(message.dify_confidence! * 100).toFixed(0)}%
                            </Badge>
                          ) : (
                            <span className="text-gray-400">-</span>
                          )}
                        </TableCell>
                      </TableRow>
                    ))}
                  </TableBody>
                </Table>

                {/* 分页 */}
                <div className="flex items-center justify-between px-6 py-4 border-t">
                  <p className="text-sm text-gray-500">
                    共 {messagesQuery.data?.total || 0} 条记录
                  </p>
                  <div className="flex space-x-2">
                    <Button
                      size="sm"
                      variant="secondary"
                      disabled={page === 1}
                      onClick={() => setPage(page - 1)}
                    >
                      上一页
                    </Button>
                    <Button
                      size="sm"
                      variant="secondary"
                      disabled={
                        !messagesQuery.data ||
                        page * pageSize >= messagesQuery.data.total
                      }
                      onClick={() => setPage(page + 1)}
                    >
                      下一页
                    </Button>
                  </div>
                </div>
              </>
            )}
          </CardContent>
        </Card>
      )}

      {/* 回复列表 */}
      {activeTab === 'replies' && (
        <Card>
          <CardHeader>
            <div className="flex items-center justify-between">
              <p className="text-sm text-gray-500">
                显示所有发送的回复记录
              </p>
              <div className="flex items-center space-x-2">
                <Filter className="w-4 h-4 text-gray-400" />
                <select
                  value={replyType}
                  onChange={(e) => {
                    setReplyType(e.target.value as 'all' | 'group' | 'private');
                    setPage(1);
                  }}
                  className="text-sm border-gray-300 rounded-md focus:ring-primary-500 focus:border-primary-500"
                >
                  <option value="all">全部类型</option>
                  <option value="group">群内回复</option>
                  <option value="private">私信</option>
                </select>
              </div>
            </div>
          </CardHeader>
          <CardContent className="p-0">
            {repliesQuery.isLoading ? (
              <Loading />
            ) : repliesQuery.data?.replies.length === 0 ? (
              <Empty message="暂无回复记录" />
            ) : (
              <>
                <Table>
                  <TableHeader>
                    <TableRow>
                      <TableHead>时间</TableHead>
                      <TableHead>类型</TableHead>
                      <TableHead>目标用户</TableHead>
                      <TableHead>回复内容</TableHead>
                      <TableHead>状态</TableHead>
                    </TableRow>
                  </TableHeader>
                  <TableBody>
                    {repliesQuery.data?.replies.map((reply) => (
                      <TableRow key={reply.id}>
                        <TableCell className="whitespace-nowrap">
                          {formatDateTime(reply.timestamp)}
                        </TableCell>
                        <TableCell>
                          <Badge variant={reply.type === 'group' ? 'info' : 'success'}>
                            {reply.type === 'group' ? '群内' : '私信'}
                          </Badge>
                        </TableCell>
                        <TableCell className="font-mono text-sm">
                          {reply.user_id}
                        </TableCell>
                        <TableCell className="max-w-md">
                          <p className="truncate" title={reply.sent_text || ''}>
                            {truncateText(reply.sent_text || '', 100)}
                          </p>
                        </TableCell>
                        <TableCell>
                          <Badge
                            variant={reply.status === 'sent' ? 'success' : 'danger'}
                          >
                            {reply.status === 'sent' ? '成功' : '失败'}
                          </Badge>
                        </TableCell>
                      </TableRow>
                    ))}
                  </TableBody>
                </Table>

                {/* 分页 */}
                <div className="flex items-center justify-between px-6 py-4 border-t">
                  <p className="text-sm text-gray-500">
                    共 {repliesQuery.data?.total || 0} 条记录
                  </p>
                  <div className="flex space-x-2">
                    <Button
                      size="sm"
                      variant="secondary"
                      disabled={page === 1}
                      onClick={() => setPage(page - 1)}
                    >
                      上一页
                    </Button>
                    <Button
                      size="sm"
                      variant="secondary"
                      disabled={
                        !repliesQuery.data ||
                        page * pageSize >= repliesQuery.data.total
                      }
                      onClick={() => setPage(page + 1)}
                    >
                      下一页
                    </Button>
                  </div>
                </div>
              </>
            )}
          </CardContent>
        </Card>
      )}
    </div>
  );
}
