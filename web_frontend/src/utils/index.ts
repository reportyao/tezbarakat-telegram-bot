import { clsx, type ClassValue } from 'clsx';
import { twMerge } from 'tailwind-merge';
import { format, formatDistanceToNow } from 'date-fns';
import { zhCN } from 'date-fns/locale';

// 合并 className
export function cn(...inputs: ClassValue[]) {
  return twMerge(clsx(inputs));
}

// 格式化日期时间
export function formatDateTime(date: string | Date): string {
  return format(new Date(date), 'yyyy-MM-dd HH:mm:ss');
}

// 格式化日期
export function formatDate(date: string | Date): string {
  return format(new Date(date), 'yyyy-MM-dd');
}

// 格式化相对时间
export function formatRelativeTime(date: string | Date): string {
  return formatDistanceToNow(new Date(date), { addSuffix: true, locale: zhCN });
}

// 格式化运行时间
export function formatUptime(seconds: number): string {
  const days = Math.floor(seconds / 86400);
  const hours = Math.floor((seconds % 86400) / 3600);
  const minutes = Math.floor((seconds % 3600) / 60);
  const secs = seconds % 60;

  const parts = [];
  if (days > 0) parts.push(`${days}天`);
  if (hours > 0) parts.push(`${hours}小时`);
  if (minutes > 0) parts.push(`${minutes}分钟`);
  if (secs > 0 || parts.length === 0) parts.push(`${secs}秒`);

  return parts.join(' ');
}

// 格式化数字
export function formatNumber(num: number): string {
  if (num >= 1000000) {
    return (num / 1000000).toFixed(1) + 'M';
  }
  if (num >= 1000) {
    return (num / 1000).toFixed(1) + 'K';
  }
  return num.toString();
}

// 截断文本
export function truncateText(text: string, maxLength: number): string {
  if (text.length <= maxLength) return text;
  return text.slice(0, maxLength) + '...';
}

// 状态颜色映射
export const statusColors: Record<string, string> = {
  active: 'bg-green-100 text-green-800',
  limited: 'bg-yellow-100 text-yellow-800',
  banned: 'bg-red-100 text-red-800',
  logging_in: 'bg-blue-100 text-blue-800',
  need_password: 'bg-purple-100 text-purple-800',
};

// 状态文本映射
export const statusTexts: Record<string, string> = {
  active: '正常',
  limited: '受限',
  banned: '封禁',
  logging_in: '登录中',
  need_password: '需要密码',
};

// 告警严重程度颜色
export const severityColors: Record<string, string> = {
  info: 'bg-blue-100 text-blue-800',
  warning: 'bg-yellow-100 text-yellow-800',
  error: 'bg-red-100 text-red-800',
};

// 日志级别颜色
export const logLevelColors: Record<string, string> = {
  DEBUG: 'text-gray-500',
  INFO: 'text-blue-600',
  WARNING: 'text-yellow-600',
  ERROR: 'text-red-600',
  CRITICAL: 'text-red-800 font-bold',
};
