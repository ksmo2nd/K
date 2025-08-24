/**
 * API Service for KSWiFi Backend Integration using Supabase
 */

import { supabase } from './supabase';
import { User as SupabaseUser } from '@supabase/supabase-js';

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
    table: string,
    method: 'SELECT' | 'INSERT' | 'UPDATE' | 'DELETE',
    data?: any,
    conditions?: any
  ): Promise<T> {
    try {
      let query = supabase.from(table);

      switch (method) {
        case 'SELECT':
          if (conditions) {
            Object.entries(conditions).forEach(([key, value]) => {
              query = query.eq(key, value);
            });
          }
          const { data: selectData, error: selectError } = await query.select();
          if (selectError) throw selectError;
          return selectData as T;

        case 'INSERT':
          const { data: insertData, error: insertError } = await query.insert(data);
          if (insertError) throw insertError;
          return insertData as T;

        case 'UPDATE':
          if (!conditions) throw new Error('Conditions required for update');
          const { data: updateData, error: updateError } = await query
            .update(data)
            .match(conditions);
          if (updateError) throw updateError;
          return updateData as T;

        case 'DELETE':
          if (!conditions) throw new Error('Conditions required for delete');
          const { data: deleteData, error: deleteError } = await query
            .delete()
            .match(conditions);
          if (deleteError) throw deleteError;
          return deleteData as T;

        default:
          throw new Error('Invalid method');
      }
    } catch (error) {
      console.error('Database operation failed:', error);
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

    await this.request('users', 'INSERT', {
      id: data.user?.id,
      email: userData.email,
      first_name: userData.first_name,
      last_name: userData.last_name,
      phone_number: userData.phone_number,
      status: 'active',
      is_admin: false,
    });

    return {
      access_token: data.session?.access_token || '',
      token_type: 'bearer',
      expires_in: 3600,
      user: data.user as unknown as User,
    };
  }

  async login(email: string, password: string): Promise<AuthResponse> {
    const { data, error } = await supabase.auth.signInWithPassword({
      email,
      password,
    });

    if (error) throw error;

    const { data: userData } = await supabase
      .from('users')
      .select('*')
      .eq('id', data.user?.id)
      .single();

    return {
      access_token: data.session?.access_token || '',
      token_type: 'bearer',
      expires_in: 3600,
      user: userData as User,
    };
  }

  async logout(): Promise<void> {
    const { error } = await supabase.auth.signOut();
    if (error) throw error;
    this.token = null;
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
    let query = supabase.from('data_packs').select('*');
    if (statusFilter) {
      query = query.eq('status', statusFilter);
    }
    const { data, error } = await query;
    if (error) throw error;
    return data as DataPack[];
  }

  async createDataPack(packData: {
    name: string;
    total_data_mb: number;
    price: number;
    currency?: string;
    expires_at: string;
  }): Promise<DataPack> {
    const { data, error } = await supabase
      .from('data_packs')
      .insert({
        ...packData,
        used_data_mb: 0,
        remaining_data_mb: packData.total_data_mb,
        status: 'active',
        currency: packData.currency || 'USD',
      })
      .single();

    if (error) throw error;
    return data as DataPack;
  }

  async recordDataUsage(packId: number, usageData: {
    data_used_mb: number;
    session_duration?: number;
    location?: string;
    device_info?: string;
  }): Promise<{ detail: string; remaining_data_mb: number; status: string }> {
    const { data: pack, error: fetchError } = await supabase
      .from('data_packs')
      .select('*')
      .eq('id', packId)
      .single();

    if (fetchError) throw fetchError;

    const newUsed = (pack.used_data_mb || 0) + usageData.data_used_mb;
    const remaining = pack.total_data_mb - newUsed;
    const status = remaining <= 0 ? 'depleted' : 'active';

    const { data, error } = await supabase
      .from('data_packs')
      .update({
        used_data_mb: newUsed,
        remaining_data_mb: Math.max(0, remaining),
        status,
      })
      .eq('id', packId)
      .single();

    if (error) throw error;

    // Record usage history
    await supabase.from('data_usage_history').insert({
      pack_id: packId,
      data_used_mb: usageData.data_used_mb,
      session_duration: usageData.session_duration,
      location: usageData.location,
      device_info: usageData.device_info,
    });

    return {
      detail: 'Usage recorded successfully',
      remaining_data_mb: Math.max(0, remaining),
      status,
    };
  }

  async getDataPackStats(): Promise<{
    total_packs: number;
    active_packs: number;
    total_data_mb: number;
    used_data_mb: number;
    remaining_data_mb: number;
    total_spent: number;
  }> {
    const { data, error } = await supabase
      .from('data_packs')
      .select('*');

    if (error) throw error;

    const stats = data.reduce((acc, pack) => ({
      total_packs: acc.total_packs + 1,
      active_packs: acc.active_packs + (pack.status === 'active' ? 1 : 0),
      total_data_mb: acc.total_data_mb + pack.total_data_mb,
      used_data_mb: acc.used_data_mb + (pack.used_data_mb || 0),
      remaining_data_mb: acc.remaining_data_mb + pack.remaining_data_mb,
      total_spent: acc.total_spent + pack.price,
    }), {
      total_packs: 0,
      active_packs: 0,
      total_data_mb: 0,
      used_data_mb: 0,
      remaining_data_mb: 0,
      total_spent: 0,
    });

    return stats;
  }

  // eSIM Management
  async getESIMs(): Promise<ESIM[]> {
    const { data, error } = await supabase
      .from('esims')
      .select('*');

    if (error) throw error;
    return data as ESIM[];
  }

  async createESIM(esimData: {
    apn?: string;
    username?: string;
    password?: string;
  }): Promise<ESIM> {
    // Generate ICCID and IMSI (simplified for example)
    const iccid = Math.random().toString(36).substring(2, 15);
    const imsi = Math.random().toString(36).substring(2, 15);
    
    const { data, error } = await supabase
      .from('esims')
      .insert({
        iccid,
        imsi,
        status: 'pending',
        apn: esimData.apn || 'default',
        username: esimData.username,
        activation_code: Math.random().toString(36).substring(2, 10),
      })
      .single();

    if (error) throw error;
    return data as ESIM;
  }

  async getESIMQRCode(esimId: number): Promise<ESIMQRCode> {
    const { data: esim, error } = await supabase
      .from('esims')
      .select('*')
      .eq('id', esimId)
      .single();

    if (error) throw error;

    // Generate QR code data (simplified)
    const qrData = {
      qr_code_data: `LPA:1$${esim.activation_code}$`,
      qr_code_image: `data:image/png;base64,${Buffer.from(esim.activation_code).toString('base64')}`,
      activation_code: esim.activation_code,
      manual_config: {
        activation_code: esim.activation_code,
        sm_dp_address: 'sm-dp.example.com',
        apn: esim.apn,
        username: esim.username,
        instructions: [
          'Open Phone Settings',
          'Go to Cellular/Mobile Data',
          'Add eSIM',
          'Scan QR Code or enter details manually',
        ],
      },
    };

    return qrData;
  }

  async activateESIM(esimId: number): Promise<ESIM> {
    const { data, error } = await supabase
      .from('esims')
      .update({
        status: 'active',
        activated_at: new Date().toISOString(),
      })
      .eq('id', esimId)
      .single();

    if (error) throw error;
    return data as ESIM;
  }

  async suspendESIM(esimId: number): Promise<{ detail: string }> {
    const { error } = await supabase
      .from('esims')
      .update({
        status: 'suspended',
      })
      .eq('id', esimId);

    if (error) throw error;
    return { detail: 'eSIM suspended successfully' };
  }

  // Health Check
  async healthCheck(): Promise<{ status: string; service: string }> {
    try {
      const { data, error } = await supabase.from('health_checks').select('created_at').limit(1);
      if (error) throw error;
      return {
        status: 'healthy',
        service: 'KSWiFi API',
      };
    } catch (error) {
      return {
        status: 'unhealthy',
        service: 'KSWiFi API',
      };
    }
  }
}

export const apiService = new ApiService();
export default apiService;