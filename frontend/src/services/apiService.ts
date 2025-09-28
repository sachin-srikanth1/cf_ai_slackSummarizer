import axios from 'axios';

const API_BASE_URL = process.env.REACT_APP_API_URL || 'http://localhost:8000';

const api = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    'Content-Type': 'application/json',
  },
});

// Request interceptor
api.interceptors.request.use(
  (config) => {
    // Add auth token if available
    const token = localStorage.getItem('authToken');
    if (token) {
      config.headers.Authorization = `Bearer ${token}`;
    }
    return config;
  },
  (error) => Promise.reject(error)
);

// Response interceptor
api.interceptors.response.use(
  (response) => response,
  (error) => {
    if (error.response?.status === 401) {
      // Handle unauthorized access
      localStorage.removeItem('authToken');
      window.location.href = '/login';
    }
    return Promise.reject(error);
  }
);

export interface SummaryRequest {
  type: 'EOD' | 'EOW';
  date_range: {
    start: string;
    end: string;
  };
  channels?: string[];
  custom_prompt?: string;
  preferences?: UserPreferences;
}

export interface SummaryResponse {
  id: string;
  summary: string;
  pdf_url: string;
  generated_at: string;
  message_count: number;
  type: 'EOD' | 'EOW';
}

export interface UserPreferences {
  summary_style: 'technical' | 'executive' | 'detailed';
  include_threads: boolean;
  filter_channels: string[];
  report_frequency: 'daily' | 'weekly';
  slack_user_id?: string;
  notification_channel?: string;
}

export interface SlackChannel {
  id: string;
  name: string;
  is_private: boolean;
  member_count?: number;
}

export interface ReportMetadata {
  id: string;
  type: 'EOD' | 'EOW';
  generated_at: string;
  message_count: number;
  channels: string[];
  pdf_available: boolean;
}

export const apiService = {
  // Health check
  async healthCheck() {
    const response = await api.get('/health');
    return response.data;
  },

  // Slack integration
  async getSlackChannels(): Promise<SlackChannel[]> {
    const response = await api.get('/api/slack/channels');
    return response.data.channels;
  },

  async syncSlackMessages() {
    const response = await api.post('/api/slack/sync');
    return response.data;
  },

  // Summary generation
  async generateSummary(request: SummaryRequest): Promise<SummaryResponse> {
    const response = await api.post('/api/summary/generate', request);
    return response.data;
  },

  async getSummaryHistory(limit = 10, offset = 0) {
    const response = await api.get(`/api/summary/history?limit=${limit}&offset=${offset}`);
    return response.data;
  },

  // Reports
  async getReports(limit = 20, offset = 0): Promise<ReportMetadata[]> {
    const response = await api.get(`/api/reports?limit=${limit}&offset=${offset}`);
    return response.data.reports;
  },

  async downloadReport(summaryId: string): Promise<Blob> {
    const response = await api.get(`/api/reports/${summaryId}/pdf`, {
      responseType: 'blob',
    });
    return response.data;
  },

  // User preferences
  async getUserPreferences(): Promise<UserPreferences> {
    const response = await api.get('/api/preferences');
    return response.data;
  },

  async updateUserPreferences(preferences: Partial<UserPreferences>) {
    const response = await api.put('/api/preferences', preferences);
    return response.data;
  },

  // Chat
  async sendChatMessage(message: string) {
    const response = await api.post('/api/chat', { message });
    return response.data;
  },

  // Scheduling
  async scheduleEODReports(enabled: boolean, time: string) {
    const response = await api.post('/api/schedule/eod', { enabled, time });
    return response.data;
  },

  async scheduleEOWReports(enabled: boolean, day: string, time: string) {
    const response = await api.post('/api/schedule/eow', { enabled, day, time });
    return response.data;
  },
};

export default apiService;