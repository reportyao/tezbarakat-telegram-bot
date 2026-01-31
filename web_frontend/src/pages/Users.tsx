import React, { useState } from 'react';
import { useQuery } from '@tanstack/react-query';
import { ExternalLink } from 'lucide-react';
import { messagesApi } from '@/services/api';
import { formatDateTime, formatRelativeTime } from '@/utils';
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

export default function Users() {
  const [page, setPage] = useState(1);
  const pageSize = 20;

  // 获取用户列表
  const { data, isLoading } = useQuery({
    queryKey: ['users', page],
    queryFn: () => messagesApi.getUsers({ page, page_size: pageSize }),
  });

  return (
    <div className="space-y-6 animate-fadeIn">
      <div className="flex items-center justify-between">
        <h1 className="text-2xl font-bold text-gray-900">用户列表</h1>
      </div>

      <Card>
        <CardHeader>
          <p className="text-sm text-gray-500">
            显示所有与 Bot 有过交互的 Telegram 用户
          </p>
        </CardHeader>
        <CardContent className="p-0">
          {isLoading ? (
            <Loading />
          ) : data?.users.length === 0 ? (
            <Empty message="暂无用户记录" />
          ) : (
            <>
              <Table>
                <TableHeader>
                  <TableRow>
                    <TableHead>用户 ID</TableHead>
                    <TableHead>用户名</TableHead>
                    <TableHead>姓名</TableHead>
                    <TableHead>收到消息数</TableHead>
                    <TableHead>最后私信时间</TableHead>
                    <TableHead>创建时间</TableHead>
                  </TableRow>
                </TableHeader>
                <TableBody>
                  {data?.users.map((user) => (
                    <TableRow key={user.user_id}>
                      <TableCell className="font-mono text-sm">
                        {user.user_id}
                      </TableCell>
                      <TableCell>
                        {user.username ? (
                          <a
                            href={`https://t.me/${user.username}`}
                            target="_blank"
                            rel="noopener noreferrer"
                            className="text-primary-600 hover:underline flex items-center"
                          >
                            @{user.username}
                            <ExternalLink className="w-3 h-3 ml-1" />
                          </a>
                        ) : (
                          <span className="text-gray-400">-</span>
                        )}
                      </TableCell>
                      <TableCell>
                        {user.first_name || user.last_name
                          ? `${user.first_name || ''} ${user.last_name || ''}`.trim()
                          : '-'}
                      </TableCell>
                      <TableCell>
                        <Badge variant="info">{user.total_messages_received}</Badge>
                      </TableCell>
                      <TableCell>
                        {user.last_private_message_time ? (
                          <span title={formatDateTime(user.last_private_message_time)}>
                            {formatRelativeTime(user.last_private_message_time)}
                          </span>
                        ) : (
                          <span className="text-gray-400">-</span>
                        )}
                      </TableCell>
                      <TableCell>{formatDateTime(user.created_at)}</TableCell>
                    </TableRow>
                  ))}
                </TableBody>
              </Table>

              {/* 分页 */}
              <div className="flex items-center justify-between px-6 py-4 border-t">
                <p className="text-sm text-gray-500">
                  共 {data?.total || 0} 位用户
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
                    disabled={!data || page * pageSize >= data.total}
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
    </div>
  );
}
