"use client"

import { useState, useEffect } from 'react'
import { useAuth } from '@/lib/auth-context'
import { supabase } from '@/lib/supabase'

interface UserProfile {
  id: string
  email: string
  first_name: string
  last_name: string
  phone_number?: string
  status: string
  is_admin: boolean
  created_at: string
  last_login?: string
}

export function useUserProfile() {
  const { user, session } = useAuth()
  const [profile, setProfile] = useState<UserProfile | null>(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    if (user) {
      fetchProfile()
    } else {
      setProfile(null)
      setLoading(false)
    }
  }, [user])

  const fetchProfile = async () => {
    try {
      setLoading(true)
      setError(null)

      const { data, error } = await supabase
        .from('users')
        .select('*')
        .eq('id', user?.id)
        .single()

      if (error) {
        throw error
      }

      setProfile(data)
    } catch (err: any) {
      console.error('Error fetching profile:', err)
      setError(err.message)
    } finally {
      setLoading(false)
    }
  }

  const updateProfile = async (updates: Partial<UserProfile>) => {
    try {
      setError(null)

      const { data, error } = await supabase
        .from('users')
        .update(updates)
        .eq('id', user?.id)
        .select()
        .single()

      if (error) {
        throw error
      }

      setProfile(data)
      return { data, error: null }
    } catch (err: any) {
      console.error('Error updating profile:', err)
      setError(err.message)
      return { data: null, error: err }
    }
  }

  return {
    profile,
    loading,
    error,
    updateProfile,
    refreshProfile: fetchProfile
  }
}