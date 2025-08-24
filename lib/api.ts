/**
 * API Service for KSWiFi Backend Integration
 */

const API_BASE_URL = process.env.NODE_ENV === 'production' 
  ? 'https://your-backend-domain.com' 
  : 'http://localhost:5000';

export interface User {
  id: number;
  email: string;
  first_name: string;
  last_name: string;
  phone_number?: string;
  status: string;
  is_admin: boolean;
  created_at: string;
  last_login?: string;
}

export interface AuthResponse {
  access_token: string;
  token_type: string;
  expires_in: number;
  user: User;
}

export interface DataPack {
  id: number;
  name: string;
  total_data_mb: number;
  used_data_mb: number;
  remaining_data_mb: number;
  price: number;
  currency: string;
  status: string;
  expires_at: string;
  created_at: string;
}

export interface ESIM {
  id: number;
  iccid: string;
  imsi: string;
  msisdn?: string;
  activation_code: string;
  status: string;
  activated_at?: string;
  created_at: string;
  apn: string;
  username?: string;
}

export interface ESIMQRCode {
  qr_code_data: string;
  qr_code_image: string;
  activation_code: string;
  manual_config: {
    activation_code: string;
    sm_dp_address: string;
    apn: string;
    username?: string;
    password?: string;
    instructions: string[];
  };
}

class ApiService {
  private token: string | null = null;

  constructor() {
    if (typeof window !== 'undefined') {
      this.token = localStorage.getItem('access_token');
    }
  }

  private getHeaders() {
    const headers: Record<string, string> = {
      'Content-Type': 'application/json',
    };
    
    if (this.token) {
      headers['Authorization'] = `Bearer ${this.token}`;
    }
    
    return headers;
  }

  private async request<T>(
    endpoint: string, 
    options: RequestInit = {}
  ): Promise<T> {
    const url = `${API_BASE_URL}${endpoint}`;
    
    const response = await fetch(url, {
      ...options,
      headers: {
        ...this.getHeaders(),
        ...options.headers,
      },
    });

    if (!response.ok) {
      const error = await response.json().catch(() => ({ detail: 'Unknown error' }));
      throw new Error(error.detail || `HTTP ${response.status}`);
    }

    return response.json();
  }

  // Authentication
  async signup(userData: {
    email: string;
    password: string;
    first_name: string;
    last_name: string;
    phone_number?: string;
  }): Promise<AuthResponse> {
    const response = await this.request<AuthResponse>('/api/auth/signup', {
      method: 'POST',
      body: JSON.stringify(userData),
    });

    this.token = response.access_token;
    if (typeof window !== 'undefined') {
      localStorage.setItem('access_token', response.access_token);
    }

    return response;
  }

  async login(email: string, password: string): Promise<AuthResponse> {
    const response = await this.request<AuthResponse>('/api/auth/login', {
      method: 'POST',
      body: JSON.stringify({ email, password }),
    });

    this.token = response.access_token;
    if (typeof window !== 'undefined') {
      localStorage.setItem('access_token', response.access_token);
    }

    return response;
  }

  async logout(): Promise<void> {
    await this.request('/api/auth/logout', { method: 'POST' });
    this.token = null;
    if (typeof window !== 'undefined') {
      localStorage.removeItem('access_token');
    }
  }

  async getCurrentUser(): Promise<User> {
    return this.request<User>('/api/auth/me');
  }

  async refreshToken(): Promise<AuthResponse> {
    const response = await this.request<AuthResponse>('/api/auth/refresh', {
      method: 'POST',
    });

    this.token = response.access_token;
    if (typeof window !== 'undefined') {
      localStorage.setItem('access_token', response.access_token);
    }

    return response;
  }

  // Data Packs
  async getDataPacks(statusFilter?: string): Promise<DataPack[]> {
    const params = statusFilter ? `?status_filter=${statusFilter}` : '';
    return this.request<DataPack[]>(`/api/datapack/${params}`);
  }

  async createDataPack(packData: {
    name: string;
    total_data_mb: number;
    price: number;
    currency?: string;
    expires_at: string;
  }): Promise<DataPack> {
    return this.request<DataPack>('/api/datapack/', {
      method: 'POST',
      body: JSON.stringify(packData),
    });
  }

  async recordDataUsage(packId: number, usageData: {
    data_used_mb: number;
    session_duration?: number;
    location?: string;
    device_info?: string;
  }): Promise<{ detail: string; remaining_data_mb: number; status: string }> {
    return this.request(`/api/datapack/${packId}/usage`, {
      method: 'POST',
      body: JSON.stringify(usageData),
    });
  }

  async getDataPackStats(): Promise<{
    total_packs: number;
    active_packs: number;
    total_data_mb: number;
    used_data_mb: number;
    remaining_data_mb: number;
    total_spent: number;
  }> {
    return this.request('/api/datapack/stats/summary');
  }

  // eSIM Management
  async getESIMs(): Promise<ESIM[]> {
    return this.request<ESIM[]>('/api/esim/');
  }

  async createESIM(esimData: {
    apn?: string;
    username?: string;
    password?: string;
  }): Promise<ESIM> {
    return this.request<ESIM>('/api/esim/', {
      method: 'POST',
      body: JSON.stringify(esimData),
    });
  }

  async getESIMQRCode(esimId: number): Promise<ESIMQRCode> {
    return this.request<ESIMQRCode>(`/api/esim/${esimId}/qr-code`);
  }

  async activateESIM(esimId: number): Promise<ESIM> {
    return this.request<ESIM>(`/api/esim/${esimId}/activate`, {
      method: 'POST',
    });
  }

  async suspendESIM(esimId: number): Promise<{ detail: string }> {
    return this.request(`/api/esim/${esimId}/suspend`, {
      method: 'POST',
    });
  }

  // Health Check
  async healthCheck(): Promise<{ status: string; service: string }> {
    return this.request('/health');
  }
}

export const apiService = new ApiService();
export default apiService;