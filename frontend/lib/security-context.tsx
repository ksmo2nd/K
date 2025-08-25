"use client"

import React, { createContext, useContext, useEffect, useState } from 'react'
import { useAuth } from './auth-context'
import { apiService } from './api'

interface SecurityState {
  isSecure: boolean
  hasValidSession: boolean
  sessionExpiryType: 'data-based' | 'never'
  dataUsagePercentage: number
  lastActivity: Date
  securityLevel: 'low' | 'medium' | 'high'
  warnings: string[]
}

interface SecurityContextType {
  security: SecurityState
  refreshSecurity: () => Promise<void>
  reportActivity: () => void
  checkSecurityCompliance: () => boolean
  getSecurityRecommendations: () => string[]
}

const SecurityContext = createContext<SecurityContextType | undefined>(undefined)

export function useAppSecurity() {
  const context = useContext(SecurityContext)
  if (!context) {
    throw new Error('useAppSecurity must be used within a SecurityProvider')
  }
  return context
}

export function SecurityProvider({ children }: { children: React.ReactNode }) {
  const { user, loading } = useAuth()
  const [security, setSecurity] = useState<SecurityState>({
    isSecure: false,
    hasValidSession: false,
    sessionExpiryType: 'data-based',
    dataUsagePercentage: 0,
    lastActivity: new Date(),
    securityLevel: 'low',
    warnings: []
  })

  const checkSessionValidity = async (): Promise<boolean> => {
    if (!user) return false
    
    try {
      // Check if the session is still valid with backend
      await apiService.healthCheck()
      return true
    } catch (error) {
      console.warn('Session validation failed:', error)
      return false
    }
  }

  const assessSecurityLevel = (lastActivity: Date): 'low' | 'medium' | 'high' => {
    const warnings = []
    
    // Check HTTPS
    const isHTTPS = window.location.protocol === 'https:'
    if (!isHTTPS && window.location.hostname !== 'localhost') {
      warnings.push('Connection is not secure (HTTP)')
    }
    
    // Check if running in development
    const isDevelopment = process.env.NODE_ENV === 'development'
    if (isDevelopment) {
      warnings.push('Running in development mode')
    }
    
    // Check session age
    const sessionAge = Date.now() - lastActivity.getTime()
    const maxSessionAge = 24 * 60 * 60 * 1000 // 24 hours
    if (sessionAge > maxSessionAge) {
      warnings.push('Session is old, consider re-authentication')
    }
    
    // Determine security level
    if (warnings.length === 0 && isHTTPS && !isDevelopment) {
      return 'high'
    } else if (warnings.length <= 1 || (isHTTPS && isDevelopment)) {
      return 'medium'
    } else {
      return 'low'
    }
  }

  const refreshSecurity = async () => {
    if (loading) return
    
    const hasValidSession = await checkSessionValidity()
    const currentTime = new Date()
    const securityLevel = assessSecurityLevel(currentTime)
    const warnings = getSecurityRecommendations()
    
    // Get data usage percentage for session expiry calculation
    let dataUsagePercentage = 0
    try {
      if (user) {
        const userProfile = await apiService.getUserProfile()
        const dataPacks = await apiService.getDataPacks()
        if (dataPacks.length > 0) {
          const totalData = dataPacks.reduce((sum, pack) => sum + pack.total_data_mb, 0)
          const usedData = dataPacks.reduce((sum, pack) => sum + pack.used_data_mb, 0)
          dataUsagePercentage = totalData > 0 ? (usedData / totalData) * 100 : 0
        }
      }
    } catch (error) {
      console.warn('Failed to get data usage for security context:', error)
    }

    setSecurity(prev => ({
      ...prev,
      isSecure: hasValidSession && securityLevel !== 'low',
      hasValidSession,
      securityLevel,
      warnings,
      sessionExpiryType: 'data-based',
      dataUsagePercentage,
      lastActivity: currentTime
    }))
  }

  const reportActivity = () => {
    setSecurity(prev => ({
      ...prev,
      lastActivity: new Date()
    }))
  }

  const checkSecurityCompliance = (): boolean => {
    return security.isSecure && 
           security.hasValidSession && 
           security.securityLevel !== 'low'
  }

  const getSecurityRecommendations = (): string[] => {
    const recommendations = []
    
    // Protocol security
    if (window.location.protocol !== 'https:' && window.location.hostname !== 'localhost') {
      recommendations.push('Use HTTPS for secure connection')
    }
    
    // Authentication recommendations
    if (!user) {
      recommendations.push('Sign in to access secure features')
    }
    
    // Session recommendations
    const sessionAge = Date.now() - security.lastActivity.getTime()
    if (sessionAge > 30 * 60 * 1000) { // 30 minutes
      recommendations.push('Session has been idle, consider refreshing')
    }
    
    // Data usage recommendations
    recommendations.push('Only download data packs on trusted networks')
    recommendations.push('Verify eSIM QR codes before installation')
    
    return recommendations
  }

  // Auto-refresh security status
  useEffect(() => {
    if (!loading) {
      refreshSecurity()
    }
  }, [user, loading])

  // Activity tracking
  useEffect(() => {
    const handleActivity = () => reportActivity()
    
    // Track user activity
    window.addEventListener('click', handleActivity)
    window.addEventListener('keydown', handleActivity)
    window.addEventListener('scroll', handleActivity)
    window.addEventListener('touchstart', handleActivity)
    
    // Periodic security refresh
    const securityInterval = setInterval(refreshSecurity, 5 * 60 * 1000) // 5 minutes
    
    return () => {
      window.removeEventListener('click', handleActivity)
      window.removeEventListener('keydown', handleActivity)
      window.removeEventListener('scroll', handleActivity)
      window.removeEventListener('touchstart', handleActivity)
      clearInterval(securityInterval)
    }
  }, [])

  const contextValue: SecurityContextType = {
    security,
    refreshSecurity,
    reportActivity,
    checkSecurityCompliance,
    getSecurityRecommendations
  }

  return (
    <SecurityContext.Provider value={contextValue}>
      {children}
    </SecurityContext.Provider>
  )
}