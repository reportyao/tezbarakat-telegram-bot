import React, { useEffect, useRef } from 'react';
import { Trash2, Download, Pause, Play } from 'lucide-react';
import { useAppStore } from '@/store';
import { formatDateTime, logLevelColors, cn } from '@/utils';
import { Button, Card, CardHeader, CardContent, Empty } from '@/components/ui';

export default function Logs() {
  const { logs, clearLogs } = useAppStore();
  const [autoScroll, setAutoScroll] = React.useState(true);
  const [filter, setFilter] = React.useState<string>('all');
  const logContainerRef = useRef<HTMLDivElement>(null);

  // 自动滚动到底部
  useEffect(() => {
    if (autoScroll && logContainerRef.current) {
      logContainerRef.current.scrollTop = logContainerRef.current.scrollHeight;
    }
  }, [logs, autoScroll]);

  // 过滤日志
  const filteredLogs = filter === 'all'
    ? logs
    : logs.filter((log) => log.level === filter);

  // 导出日志
  const handleExport = () => {
    const content = filteredLogs
      .map((log) => `[${log.timestamp}] [${log.level}] ${log.module ? `[${log.module}] ` : ''}${log.message}`)
      .join('\n');
    
    const blob = new Blob([content], { type: 'text/plain' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `logs_${new Date().toISOString().slice(0, 10)}.txt`;
    a.click();
    URL.revokeObjectURL(url);
  };

  return (
    <div className="space-y-6 animate-fadeIn">
      <div className="flex items-center justify-between">
        <h1 className="text-2xl font-bold text-gray-900">实时日志</h1>
        <div className="flex space-x-2">
          <Button
            variant="secondary"
            onClick={() => setAutoScroll(!autoScroll)}
          >
            {autoScroll ? (
              <>
                <Pause className="w-4 h-4 mr-2" />
                暂停滚动
              </>
            ) : (
              <>
                <Play className="w-4 h-4 mr-2" />
                自动滚动
              </>
            )}
          </Button>
          <Button variant="secondary" onClick={handleExport}>
            <Download className="w-4 h-4 mr-2" />
            导出
          </Button>
          <Button variant="danger" onClick={clearLogs}>
            <Trash2 className="w-4 h-4 mr-2" />
            清空
          </Button>
        </div>
      </div>

      <Card>
        <CardHeader>
          <div className="flex items-center justify-between">
            <p className="text-sm text-gray-500">
              实时显示 Bot 运行日志（通过 WebSocket 推送）
            </p>
            <select
              value={filter}
              onChange={(e) => setFilter(e.target.value)}
              className="text-sm border-gray-300 rounded-md focus:ring-primary-500 focus:border-primary-500"
            >
              <option value="all">全部级别</option>
              <option value="DEBUG">DEBUG</option>
              <option value="INFO">INFO</option>
              <option value="WARNING">WARNING</option>
              <option value="ERROR">ERROR</option>
            </select>
          </div>
        </CardHeader>
        <CardContent className="p-0">
          {filteredLogs.length === 0 ? (
            <Empty message="暂无日志，等待 WebSocket 连接..." />
          ) : (
            <div
              ref={logContainerRef}
              className="h-[600px] overflow-y-auto bg-gray-900 p-4 font-mono text-sm"
            >
              {filteredLogs.map((log, index) => (
                <div
                  key={index}
                  className="py-1 border-b border-gray-800 last:border-0"
                >
                  <span className="text-gray-500">
                    [{log.timestamp}]
                  </span>
                  <span className={cn('ml-2', logLevelColors[log.level] || 'text-gray-400')}>
                    [{log.level}]
                  </span>
                  {log.module && (
                    <span className="ml-2 text-purple-400">
                      [{log.module}]
                    </span>
                  )}
                  <span className="ml-2 text-gray-300">
                    {log.message}
                  </span>
                </div>
              ))}
            </div>
          )}
        </CardContent>
      </Card>

      {/* 连接状态 */}
      <div className="text-center text-sm text-gray-500">
        <span className="inline-flex items-center">
          <span className="w-2 h-2 mr-2 bg-green-500 rounded-full animate-pulse" />
          WebSocket 已连接 | 已接收 {logs.length} 条日志
        </span>
      </div>
    </div>
  );
}
