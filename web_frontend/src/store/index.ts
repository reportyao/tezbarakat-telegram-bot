import { create } from 'zustand';
import type { BotStatus, Alert, LogEntry } from '@/types';

interface AppState {
  // 认证状态
  isAuthenticated: boolean;
  setAuthenticated: (value: boolean) => void;

  // Bot 状态
  botStatus: BotStatus | null;
  setBotStatus: (status: BotStatus | null) => void;

  // 告警
  unreadAlerts: number;
  setUnreadAlerts: (count: number) => void;
  recentAlerts: Alert[];
  addAlert: (alert: Alert) => void;

  // 日志
  logs: LogEntry[];
  addLog: (log: LogEntry) => void;
  clearLogs: () => void;

  // UI 状态
  sidebarOpen: boolean;
  setSidebarOpen: (open: boolean) => void;
}

export const useAppStore = create<AppState>((set) => ({
  // 认证状态
  isAuthenticated: !!localStorage.getItem('token'),
  setAuthenticated: (value) => set({ isAuthenticated: value }),

  // Bot 状态
  botStatus: null,
  setBotStatus: (status) => set({ botStatus: status }),

  // 告警
  unreadAlerts: 0,
  setUnreadAlerts: (count) => set({ unreadAlerts: count }),
  recentAlerts: [],
  addAlert: (alert) =>
    set((state) => ({
      recentAlerts: [alert, ...state.recentAlerts].slice(0, 50),
      unreadAlerts: state.unreadAlerts + 1,
    })),

  // 日志
  logs: [],
  addLog: (log) =>
    set((state) => ({
      logs: [log, ...state.logs].slice(0, 500),
    })),
  clearLogs: () => set({ logs: [] }),

  // UI 状态
  sidebarOpen: true,
  setSidebarOpen: (open) => set({ sidebarOpen: open }),
}));
