/**
 * API Service for KSWiFi App using Hybrid Supabase + FastAPI
 */

import { supabase } from './supabase';
import { User as SupabaseUser } from '@supabase/supabase-js';

// Backend API URL - REQUIRES environment variable in production
const backendUrl = process.env.NEXT_PUBLIC_BACKEND_URL;

if (!backendUrl) {
  // Allow build to complete but warn about missing environment variable
  console.warn(
    '⚠️  MISSING ENVIRONMENT VARIABLE: NEXT_PUBLIC_BACKEND_URL\n' +
    'Please set this to your FastAPI backend URL in production.\n' +
    'Using placeholder for build process.'
  );
}

// Use environment variable or build-time placeholder
const BACKEND_URL = backendUrl || 'https://your-backend-url.com';

export interface User {
  id: string;
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
  id: string;
  user_id: string;
  name: string;
  total_data_mb: number;
  used_data_mb: number;
  remaining_data_mb: number;
  price: number;
  currency: string;
  status: string;
  expires_at: string;
  created_at: string;
  updated_at: string;
}

export interface ESIM {
  id: string;
  user_id: string;
  iccid: string;
  imsi: string;
  msisdn?: string;
  activation_code: string;
  qr_code_data: string;
  status: string;
  activated_at?: string;
  created_at: string;
  updated_at: string;
  apn: string;
  username?: string;
  password?: string;
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
  // Helper method to get current user
  private async getCurrentUserId(): Promise<string> {
    const { data: { session }, error } = await supabase.auth.getSession();
    if (error) throw error;
    if (!session?.user) throw new Error('No user logged in');
    return session.user.id;
  }

  // Helper method to get auth token for backend calls
  private async getAuthToken(): Promise<string> {
    const { data: { session }, error } = await supabase.auth.getSession();
    if (error) throw error;
    if (!session?.access_token) throw new Error('No auth token available');
    return session.access_token;
  }

  // Helper method to make authenticated requests to backend API
  private async makeBackendRequest<T>(
    endpoint: string,
    options: RequestInit = {}
  ): Promise<T> {
    try {
      const token = await this.getAuthToken();
      
      const response = await fetch(`${BACKEND_URL}/api${endpoint}`, {
        ...options,
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${token}`,
          ...options.headers,
        },
      });

      if (!response.ok) {
        const error = await response.json().catch(() => ({}));
        throw new Error(error.detail || `HTTP ${response.status}: ${response.statusText}`);
      }

      return await response.json();
    } catch (error) {
      console.error('Backend API request failed:', error);
      throw error;
    }
  }

  // Authentication
  async signup(userData: {
    email: string;
    password: string;
    first_name: string;
    last_name: string;
    phone_number?: string;
  }): Promise<AuthResponse> {
    const { data, error } = await supabase.auth.signUp({
      email: userData.email,
      password: userData.password,
      options: {
        data: {
          first_name: userData.first_name,
          last_name: userData.last_name,
          phone_number: userData.phone_number,
        }
      }
    });

    if (error) throw error;

    if (data.user) {
      // Insert user profile data
      const { error: profileError } = await supabase
        .from('users')
        .insert({
          id: data.user.id,
          email: userData.email,
          first_name: userData.first_name,
          last_name: userData.last_name,
          phone_number: userData.phone_number,
          status: 'active',
          is_admin: false,
        });

      if (profileError) throw profileError;

      // Trigger backend post-signup webhook
      try {
        await fetch(`${BACKEND_URL}/api/auth/webhook/signup`, {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ user_id: data.user.id })
        });
      } catch (e) {
        console.warn('Backend signup webhook failed:', e);
      }
    }

    return {
      access_token: data.session?.access_token || '',
      token_type: 'bearer',
      expires_in: data.session?.expires_in || 3600,
      user: {
        id: data.user?.id || '',
        email: userData.email,
        first_name: userData.first_name,
        last_name: userData.last_name,
        phone_number: userData.phone_number,
        status: 'active',
        is_admin: false,
        created_at: new Date().toISOString(),
      },
    };
  }

  async login(email: string, password: string): Promise<AuthResponse> {
    const { data, error } = await supabase.auth.signInWithPassword({
      email,
      password,
    });

    if (error) throw error;

    // Trigger backend post-login webhook
    if (data.user) {
      try {
        await fetch(`${BACKEND_URL}/api/auth/webhook/login`, {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ user_id: data.user.id })
        });
      } catch (e) {
        console.warn('Backend login webhook failed:', e);
      }
    }

    const { data: userData, error: userError } = await supabase
      .from('users')
      .select('*')
      .eq('id', data.user?.id)
      .single();

    if (userError) throw userError;

    return {
      access_token: data.session?.access_token || '',
      token_type: 'bearer',
      expires_in: data.session?.expires_in || 3600,
      user: userData as User,
    };
  }

  async logout(): Promise<void> {
    const { error } = await supabase.auth.signOut();
    if (error) throw error;
  }

  async getCurrentUser(): Promise<User> {
    const { data: { session }, error } = await supabase.auth.getSession();
    if (error) throw error;
    if (!session?.user) throw new Error('No user logged in');

    const { data, error: userError } = await supabase
      .from('users')
      .select('*')
      .eq('id', session.user.id)
      .single();

    if (userError) throw userError;
    return data as User;
  }

  async refreshToken(): Promise<AuthResponse> {
    const { data, error } = await supabase.auth.refreshSession();
    if (error) throw error;

    const { data: userData, error: userError } = await supabase
      .from('users')
      .select('*')
      .eq('id', data.user?.id)
      .single();

    if (userError) throw userError;

    return {
      access_token: data.session?.access_token || '',
      token_type: 'bearer',
      expires_in: data.session?.expires_in || 3600,
      user: userData as User,
    };
  }

  // Internet Sessions - Core KSWiFi functionality
  async getAvailableSessions(): Promise<any[]> {
    const response = await this.makeBackendRequest<any[]>('/sessions/available');
    return response;
  }

  async startSessionDownload(sessionId: string, esimId?: string): Promise<any> {
    const response = await this.makeBackendRequest<any>('/sessions/download', {
      method: 'POST',
      body: JSON.stringify({
        session_id: sessionId,
        esim_id: esimId
      })
    });
    return response;
  }

  async activateSession(sessionId: string): Promise<any> {
    const response = await this.makeBackendRequest<any>('/sessions/activate', {
      method: 'POST',
      body: JSON.stringify({
        session_id: sessionId
      })
    });
    return response;
  }

  async getMySessions(): Promise<any[]> {
    const response = await this.makeBackendRequest<any[]>('/sessions/my-sessions');
    return response;
  }

  async getSessionStatus(sessionId: string): Promise<any> {
    const response = await this.makeBackendRequest<any>(`/sessions/${sessionId}/status`);
    return response;
  }

  async trackSessionUsage(sessionId: string, dataUsedMb: number): Promise<any> {
    const response = await this.makeBackendRequest<any>('/sessions/track-usage', {
      method: 'POST',
      body: JSON.stringify({
        session_id: sessionId,
        data_used_mb: dataUsedMb
      })
    });
    return response;
  }

  async getFreeQuotaUsage(): Promise<any> {
    const response = await this.makeBackendRequest<any>('/sessions/quota/free');
    return response;
  }

  // Data Packs - Legacy support for backward compatibility
  async getDataPacks(statusFilter?: string): Promise<DataPack[]> {
    const userId = await this.getCurrentUserId();
    const response = await this.makeBackendRequest<{ packs: DataPack[]; count: number }>(`/bundles/user/${userId}/packs${statusFilter ? `?status=${statusFilter}` : ''}`);
    return response.packs;
  }

  async getAvailableBundles(): Promise<any> {
    const response = await this.makeBackendRequest<any>('/bundles/available');
    return response;
  }

  async calculateBundlePrice(data_mb: number, validity_days: number = 30): Promise<any> {
    const response = await this.makeBackendRequest<any>(`/bundles/calculate-price?data_mb=${data_mb}&validity_days=${validity_days}`, {
      method: 'POST'
    });
    return response;
  }

  async createDataPack(packData: {
    bundle_name?: string;
    custom_mb?: number;
    validity_days?: number;
  }): Promise<any> {
    const userId = await this.getCurrentUserId();
    
    const response = await this.makeBackendRequest<any>('/bundles/create', {
      method: 'POST',
      body: JSON.stringify({
        user_id: userId,
        ...packData
      })
    });
    
    return response;
  }

  async recordDataUsage(usageData: {
    data_used_mb: number;
    session_duration?: number;
    location?: string;
    device_info?: string;
  }): Promise<any> {
    const userId = await this.getCurrentUserId();
    
    const response = await this.makeBackendRequest<any>('/bundles/usage/update', {
      method: 'POST',
      body: JSON.stringify({
        user_id: userId,
        ...usageData
      })
    });
    
    return response;
  }

  async getDataPackStats(): Promise<any> {
    const userId = await this.getCurrentUserId();
    const response = await this.makeBackendRequest<any>(`/bundles/user/${userId}/summary`);
    return response;
  }

  // eSIM Management - Now using backend API for provider integration
  async getESIMs(): Promise<ESIM[]> {
    const userId = await this.getCurrentUserId();
    const response = await this.makeBackendRequest<{ esims: ESIM[]; count: number }>(`/esim/user/${userId}`);
    return response.esims;
  }

  async provisionESIM(bundle_size_mb: number): Promise<any> {
    const userId = await this.getCurrentUserId();
    
    const response = await this.makeBackendRequest<any>('/esim/provision', {
      method: 'POST',
      body: JSON.stringify({
        user_id: userId,
        bundle_size_mb
      })
    });
    
    return response;
  }

  async getESIMQRCode(esimId: string): Promise<ESIMQRCode> {
    const response = await this.makeBackendRequest<ESIMQRCode>(`/esim/${esimId}/qr-code`);
    return response;
  }

  async activateESIM(esimId: string): Promise<any> {
    const response = await this.makeBackendRequest<any>(`/esim/${esimId}/activate`, {
      method: 'POST'
    });
    return response;
  }

  async suspendESIM(esimId: string): Promise<{ detail: string }> {
    const response = await this.makeBackendRequest<{ detail: string }>(`/esim/${esimId}/suspend`, {
      method: 'POST'
    });
    return response;
  }

  async getESIMUsage(esimId: string): Promise<any> {
    const response = await this.makeBackendRequest<any>(`/esim/${esimId}/usage`);
    return response;
  }

  async getESIMStatus(esimId: string): Promise<any> {
    const response = await this.makeBackendRequest<any>(`/esim/${esimId}/status`);
    return response;
  }

  // Notifications
  async getNotifications(limit: number = 50, unread_only: boolean = false): Promise<any> {
    const userId = await this.getCurrentUserId();
    const response = await this.makeBackendRequest<any>(`/notifications/user/${userId}?limit=${limit}&unread_only=${unread_only}`);
    return response;
  }

  async markNotificationRead(notification_id: string): Promise<any> {
    const userId = await this.getCurrentUserId();
    const response = await this.makeBackendRequest<any>('/notifications/mark-read', {
      method: 'POST',
      body: JSON.stringify({
        notification_id,
        user_id: userId
      })
    });
    return response;
  }

  async markAllNotificationsRead(): Promise<any> {
    const userId = await this.getCurrentUserId();
    const response = await this.makeBackendRequest<any>(`/notifications/user/${userId}/mark-all-read`, {
      method: 'POST'
    });
    return response;
  }

  async getUnreadNotificationCount(): Promise<{ unread_count: number }> {
    const userId = await this.getCurrentUserId();
    const response = await this.makeBackendRequest<{ unread_count: number }>(`/notifications/user/${userId}/unread-count`);
    return response;
  }

  // Device registration for push notifications
  async registerDevice(push_token: string, device_type: 'ios' | 'android' | 'web'): Promise<any> {
    const userId = await this.getCurrentUserId();
    const response = await this.makeBackendRequest<any>('/auth/device/register', {
      method: 'POST',
      body: JSON.stringify({
        user_id: userId,
        push_token,
        device_type
      })
    });
    return response;
  }

  // Monitoring
  async getMonitoringStats(): Promise<any> {
    const response = await this.makeBackendRequest<any>('/monitoring/stats');
    return response;
  }

  // eSIM Generation
  async generateESIM(sessionId?: string, dataPackSizeMb: number = 1024): Promise<{
    success: boolean;
    esim_id: string;
    iccid: string;
    imsi: string;
    carrier_name: string;
    carrier_plmn: string;
    activation_code: string;
    qr_code_data: string;
    qr_code_image: string;
    data_pack_id?: string;
    profile_data: any;
    installation_instructions: string[];
    message: string;
  }> {
    const response = await this.makeBackendRequest<any>('/esim/generate-esim', {
      method: 'POST',
      body: JSON.stringify({
        session_id: sessionId,
        data_pack_size_mb: dataPackSizeMb,
        carrier_name: 'KSWiFi',
        carrier_plmn: '99999'
      })
    });
    return response;
  }

  // Health Check
  async healthCheck(): Promise<{ status: string; service: string; [key: string]: string }> {
    try {
      // Check both Supabase and backend
      const supabaseHealth = await supabase.from('users').select('id').limit(1);
      const backendHealth = await this.makeBackendRequest<any>('/monitoring/health');
      
      return {
        status: 'healthy',
        service: 'KSWiFi App (Hybrid)',
        supabase: supabaseHealth.error ? 'unhealthy' : 'healthy',
        backend: backendHealth.status || 'healthy'
      };
    } catch (error) {
      return {
        status: 'unhealthy',
        service: 'KSWiFi App (Hybrid)',
        error: error instanceof Error ? error.message : 'Unknown error'
      };
    }
  }
}

export const apiService = new ApiService();
export const api = apiService; // Alias for compatibility
export default apiService;