import axios, { AxiosInstance, AxiosError } from 'axios';
import type {
  Account, Group, Keyword, User, Message, Reply, Config, Alert,
  DashboardData, BotStatus, LoginRequest, TokenResponse, BaseResponse
} from '@/types';

// 创建 axios 实例
const api: AxiosInstance = axios.create({
  baseURL: '/api',
  timeout: 30000,
  headers: {
    'Content-Type': 'application/json',
  },
});

// 请求拦截器
api.interceptors.request.use(
  (config) => {
    const token = localStorage.getItem('token');
    if (token) {
      config.headers.Authorization = `Bearer ${token}`;
    }
    return config;
  },
  (error) => Promise.reject(error)
);

// 响应拦截器
api.interceptors.response.use(
  (response) => response,
  (error: AxiosError) => {
    if (error.response?.status === 401) {
      localStorage.removeItem('token');
      window.location.href = '/login';
    }
    return Promise.reject(error);
  }
);

// =====================================================
// 认证 API
// =====================================================

export const authApi = {
  login: async (data: LoginRequest): Promise<TokenResponse> => {
    const response = await api.post<TokenResponse>('/auth/login', data);
    return response.data;
  },

  logout: async (): Promise<BaseResponse> => {
    const response = await api.post<BaseResponse>('/auth/logout');
    return response.data;
  },

  getCurrentUser: async () => {
    const response = await api.get('/auth/me');
    return response.data;
  },
};

// =====================================================
// 仪表盘 API
// =====================================================

export const dashboardApi = {
  getData: async (): Promise<DashboardData> => {
    const response = await api.get<DashboardData>('/dashboard');
    return response.data;
  },

  getBotStatus: async (): Promise<BotStatus> => {
    const response = await api.get<BotStatus>('/bot/status');
    return response.data;
  },

  controlBot: async (action: 'start' | 'stop' | 'restart'): Promise<BaseResponse> => {
    const response = await api.post<BaseResponse>('/bot/control', { action });
    return response.data;
  },

  testDify: async (): Promise<BaseResponse> => {
    const response = await api.post<BaseResponse>('/bot/test-dify');
    return response.data;
  },
};

// =====================================================
// 账号 API
// =====================================================

export const accountsApi = {
  getAll: async (): Promise<{ accounts: Account[] }> => {
    const response = await api.get('/accounts');
    return response.data;
  },

  create: async (data: { phone_number: string; session_name: string }): Promise<Account> => {
    const response = await api.post<Account>('/accounts', data);
    return response.data;
  },

  startLogin: async (id: number): Promise<{ status: string; phone_code_hash?: string }> => {
    const response = await api.post(`/accounts/${id}/login/start`);
    return response.data;
  },

  completeLogin: async (id: number, data: { code?: string; password?: string }): Promise<BaseResponse> => {
    const response = await api.post<BaseResponse>(`/accounts/${id}/login/complete`, data);
    return response.data;
  },

  reconnect: async (id: number): Promise<BaseResponse> => {
    const response = await api.post<BaseResponse>(`/accounts/${id}/reconnect`);
    return response.data;
  },

  checkHealth: async (id: number): Promise<{ healthy: boolean; message: string }> => {
    const response = await api.get(`/accounts/${id}/health`);
    return response.data;
  },

  delete: async (id: number): Promise<BaseResponse> => {
    const response = await api.delete<BaseResponse>(`/accounts/${id}`);
    return response.data;
  },
};

// =====================================================
// 群组 API
// =====================================================

export const groupsApi = {
  getAll: async (): Promise<{ groups: Group[] }> => {
    const response = await api.get('/groups');
    return response.data;
  },

  resolve: async (username: string): Promise<{ group_id: number; title: string; username?: string }> => {
    const response = await api.get('/groups/resolve', { params: { username } });
    return response.data;
  },

  create: async (data: { group_id: number; group_name: string; group_username?: string }): Promise<Group> => {
    const response = await api.post<Group>('/groups', data);
    return response.data;
  },

  update: async (id: number, data: { is_active?: boolean; group_name?: string }): Promise<Group> => {
    const response = await api.put<Group>(`/groups/${id}`, data);
    return response.data;
  },

  delete: async (id: number): Promise<BaseResponse> => {
    const response = await api.delete<BaseResponse>(`/groups/${id}`);
    return response.data;
  },
};

// =====================================================
// 关键词 API
// =====================================================

export const keywordsApi = {
  getAll: async (): Promise<{ keywords: Keyword[] }> => {
    const response = await api.get('/keywords');
    return response.data;
  },

  create: async (data: { keyword: string }): Promise<Keyword> => {
    const response = await api.post<Keyword>('/keywords', data);
    return response.data;
  },

  update: async (id: number, data: { is_active?: boolean }): Promise<Keyword> => {
    const response = await api.put<Keyword>(`/keywords/${id}`, data);
    return response.data;
  },

  delete: async (id: number): Promise<BaseResponse> => {
    const response = await api.delete<BaseResponse>(`/keywords/${id}`);
    return response.data;
  },

  batchCreate: async (keywords: string[]): Promise<BaseResponse> => {
    const response = await api.post<BaseResponse>('/keywords/batch', { keywords });
    return response.data;
  },
};

// =====================================================
// 消息 API
// =====================================================

export const messagesApi = {
  getMessages: async (params: {
    page?: number;
    page_size?: number;
    group_id?: number;
    user_id?: number;
    triggered_only?: boolean;
  }): Promise<{ total: number; messages: Message[] }> => {
    const response = await api.get('/messages', { params });
    return response.data;
  },

  getReplies: async (params: {
    page?: number;
    page_size?: number;
    reply_type?: 'group' | 'private';
    account_id?: number;
    user_id?: number;
  }): Promise<{ total: number; replies: Reply[] }> => {
    const response = await api.get('/replies', { params });
    return response.data;
  },

  getUsers: async (params: {
    page?: number;
    page_size?: number;
  }): Promise<{ total: number; users: User[] }> => {
    const response = await api.get('/users', { params });
    return response.data;
  },
};

// =====================================================
// 配置 API
// =====================================================

export const configApi = {
  getAll: async (): Promise<{ configs: Config[] }> => {
    const response = await api.get('/config');
    return response.data;
  },

  update: async (key: string, value: any): Promise<Config> => {
    const response = await api.put<Config>(`/config/${key}`, { value });
    return response.data;
  },

  batchUpdate: async (configs: Record<string, any>): Promise<BaseResponse> => {
    const response = await api.put<BaseResponse>('/config', { configs });
    return response.data;
  },
};

// =====================================================
// 告警 API
// =====================================================

export const alertsApi = {
  getAll: async (params: {
    page?: number;
    page_size?: number;
    unread_only?: boolean;
  }): Promise<{ total: number; unread_count: number; alerts: Alert[] }> => {
    const response = await api.get('/alerts', { params });
    return response.data;
  },

  markRead: async (alertIds: number[]): Promise<BaseResponse> => {
    const response = await api.post<BaseResponse>('/alerts/read', { alert_ids: alertIds });
    return response.data;
  },

  markAllRead: async (): Promise<BaseResponse> => {
    const response = await api.post<BaseResponse>('/alerts/read-all');
    return response.data;
  },
};

export default api;
