import axios from 'axios';

const API_BASE_URL = 'http://localhost:8000/api';

export const apiClient = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    'Content-Type': 'application/json',
  },
  timeout: 45000, // 45s timeout (Rule 6)
});

// Types
export interface EmailThread {
  thread_id: string;
  subject?: string;
  sender?: string;
  snippet?: string;
  date?: string;
  status: 'new' | 'processed' | 'replied';
  // Extended fields from API
  influencer_name?: string;
  brand?: string;
  category?: string;
  latest_message_time?: string;
}

export interface EmailDetail extends EmailThread {
  messages: EmailMessage[];
}

export interface EmailMessage {
  id?: string;
  sender?: string;
  from?: string;
  content?: string;
  body?: string;
  date?: string;
  timestamp?: string;
}

export interface GeneratedResponse {
  category: string;
  response_draft: string;
  pricing_breakdown?: any;
}

// API Functions
export const emailApi = {
  listEmails: async (limit: number = 20): Promise<EmailThread[]> => {
    const response = await apiClient.get(`/emails?limit=${limit}`);
    return response.data.data;
  },

  getThread: async (threadId: string): Promise<EmailDetail> => {
    const response = await apiClient.get(`/emails/${threadId}`);
    return response.data.data;
  },

  generateResponse: async (threadId: string, brandId: string = 'perplexity'): Promise<GeneratedResponse> => {
    const response = await apiClient.post('/generate', { thread_id: threadId, brand_id: brandId });
    return response.data;
  },

  sendReply: async (threadId: string, content: string): Promise<any> => {
    const response = await apiClient.post('/send', { thread_id: threadId, content });
    return response.data;
  }
};
