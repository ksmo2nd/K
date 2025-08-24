/**
 * API Service for KSWiFi App using Supabase
 */

import { supabase } from './supabase';
import { User as SupabaseUser } from '@supabase/supabase-js';

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

    // Update last login time
    if (data.user) {
      await supabase
        .from('users')
        .update({ last_login: new Date().toISOString() })
        .eq('id', data.user.id);
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

  // Data Packs
  async getDataPacks(statusFilter?: string): Promise<DataPack[]> {
    const userId = await this.getCurrentUserId();
    let query = supabase.from('data_packs').select('*').eq('user_id', userId);
    
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
    const userId = await this.getCurrentUserId();
    
    const { data, error } = await supabase
      .from('data_packs')
      .insert({
        user_id: userId,
        ...packData,
        used_data_mb: 0,
        remaining_data_mb: packData.total_data_mb,
        status: 'active',
        currency: packData.currency || 'USD',
      })
      .select()
      .single();

    if (error) throw error;
    return data as DataPack;
  }

  async recordDataUsage(packId: string, usageData: {
    data_used_mb: number;
    session_duration?: number;
    location?: string;
    device_info?: string;
  }): Promise<{ detail: string; remaining_data_mb: number; status: string }> {
    const userId = await this.getCurrentUserId();
    
    const { data: pack, error: fetchError } = await supabase
      .from('data_packs')
      .select('*')
      .eq('id', packId)
      .eq('user_id', userId)
      .single();

    if (fetchError) throw fetchError;

    const newUsed = (pack.used_data_mb || 0) + usageData.data_used_mb;
    const remaining = pack.total_data_mb - newUsed;
    const status = remaining <= 0 ? 'exhausted' : pack.status;

    const { error } = await supabase
      .from('data_packs')
      .update({
        used_data_mb: newUsed,
        remaining_data_mb: Math.max(0, remaining),
        status,
      })
      .eq('id', packId)
      .eq('user_id', userId);

    if (error) throw error;

    // Record usage history
    await supabase.from('usage_logs').insert({
      user_id: userId,
      data_pack_id: packId,
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
    const userId = await this.getCurrentUserId();
    
    const { data, error } = await supabase
      .from('data_packs')
      .select('*')
      .eq('user_id', userId);

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
    const userId = await this.getCurrentUserId();
    
    const { data, error } = await supabase
      .from('esims')
      .select('*')
      .eq('user_id', userId);

    if (error) throw error;
    return data as ESIM[];
  }

  async createESIM(esimData: {
    apn?: string;
    username?: string;
    password?: string;
  }): Promise<ESIM> {
    const userId = await this.getCurrentUserId();
    
    // Generate ICCID and IMSI (simplified for example)
    const iccid = `8901240${Math.random().toString().substring(2, 15)}`;
    const imsi = `901240${Math.random().toString().substring(2, 15)}`;
    const activationCode = `LPA:1$sm-dp.kswifi.com$${Math.random().toString(36).substring(2, 10)}`;
    
    const { data, error } = await supabase
      .from('esims')
      .insert({
        user_id: userId,
        iccid,
        imsi,
        status: 'pending',
        apn: esimData.apn || 'internet',
        username: esimData.username,
        password: esimData.password,
        activation_code: Math.random().toString(36).substring(2, 10),
        qr_code_data: activationCode,
      })
      .select()
      .single();

    if (error) throw error;
    return data as ESIM;
  }

  async getESIMQRCode(esimId: string): Promise<ESIMQRCode> {
    const userId = await this.getCurrentUserId();
    
    const { data: esim, error } = await supabase
      .from('esims')
      .select('*')
      .eq('id', esimId)
      .eq('user_id', userId)
      .single();

    if (error) throw error;

    // Generate QR code data using proper LPA format
    const qrData = {
      qr_code_data: esim.qr_code_data,
      qr_code_image: `data:image/svg+xml;base64,${btoa(`<svg xmlns="http://www.w3.org/2000/svg" width="200" height="200"><rect width="200" height="200" fill="white"/><text x="100" y="100" text-anchor="middle" font-family="monospace" font-size="8">QR Code: ${esim.activation_code}</text></svg>`)}`,
      activation_code: esim.activation_code,
      manual_config: {
        activation_code: esim.activation_code,
        sm_dp_address: 'sm-dp.kswifi.com',
        apn: esim.apn,
        username: esim.username,
        password: esim.password,
        instructions: [
          'Open Phone Settings',
          'Go to Cellular/Mobile Data',
          'Add eSIM',
          'Scan QR Code or enter details manually',
          'Follow the on-screen instructions',
        ],
      },
    };

    return qrData;
  }

  async activateESIM(esimId: string): Promise<ESIM> {
    const userId = await this.getCurrentUserId();
    
    const { data, error } = await supabase
      .from('esims')
      .update({
        status: 'active',
        activated_at: new Date().toISOString(),
      })
      .eq('id', esimId)
      .eq('user_id', userId)
      .select()
      .single();

    if (error) throw error;
    return data as ESIM;
  }

  async suspendESIM(esimId: string): Promise<{ detail: string }> {
    const userId = await this.getCurrentUserId();
    
    const { error } = await supabase
      .from('esims')
      .update({
        status: 'suspended',
      })
      .eq('id', esimId)
      .eq('user_id', userId);

    if (error) throw error;
    return { detail: 'eSIM suspended successfully' };
  }

  // Health Check
  async healthCheck(): Promise<{ status: string; service: string }> {
    try {
      const { data, error } = await supabase.from('users').select('id').limit(1);
      if (error) throw error;
      return {
        status: 'healthy',
        service: 'KSWiFi App (Supabase)',
      };
    } catch (error) {
      return {
        status: 'unhealthy',
        service: 'KSWiFi App (Supabase)',
      };
    }
  }
}

export const apiService = new ApiService();
export default apiService;