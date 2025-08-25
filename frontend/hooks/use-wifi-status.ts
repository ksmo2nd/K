"use client"

import { useState, useEffect } from 'react'

interface WiFiStatus {
  isConnected: boolean
  networkName?: string
  signalStrength?: number
  connectionType?: 'wifi' | 'cellular' | 'ethernet' | 'none'
  isOnline: boolean
}

/**
 * Hook to detect real WiFi/network connection status
 * Uses modern browser APIs to determine actual connectivity
 */
export function useWiFiStatus(): WiFiStatus {
  const [wifiStatus, setWiFiStatus] = useState<WiFiStatus>({
    isConnected: false,
    networkName: undefined,
    signalStrength: undefined,
    connectionType: 'none',
    isOnline: navigator.onLine
  })

  useEffect(() => {
    // Check initial connection status
    updateConnectionStatus()

    // Listen for online/offline events
    const handleOnline = () => {
      updateConnectionStatus()
    }

    const handleOffline = () => {
      setWiFiStatus(prev => ({
        ...prev,
        isConnected: false,
        isOnline: false,
        connectionType: 'none'
      }))
    }

    // Listen for connection changes
    window.addEventListener('online', handleOnline)
    window.addEventListener('offline', handleOffline)

    // Modern browsers support Network Information API
    if ('connection' in navigator) {
      const connection = (navigator as any).connection
      const handleConnectionChange = () => {
        updateConnectionStatus()
      }
      connection.addEventListener('change', handleConnectionChange)

      return () => {
        window.removeEventListener('online', handleOnline)
        window.removeEventListener('offline', handleOffline)
        connection.removeEventListener('change', handleConnectionChange)
      }
    }

    return () => {
      window.removeEventListener('online', handleOnline)
      window.removeEventListener('offline', handleOffline)
    }
  }, [])

  const updateConnectionStatus = async () => {
    const isOnline = navigator.onLine

    if (!isOnline) {
      setWiFiStatus({
        isConnected: false,
        networkName: undefined,
        signalStrength: undefined,
        connectionType: 'none',
        isOnline: false
      })
      return
    }

    // Try to determine connection type using Network Information API
    let connectionType: 'wifi' | 'cellular' | 'ethernet' | 'none' = 'none'
    let effectiveType = 'unknown'

    if ('connection' in navigator) {
      const connection = (navigator as any).connection
      effectiveType = connection.effectiveType || 'unknown'
      
      // Map connection types
      if (connection.type) {
        switch (connection.type) {
          case 'wifi':
            connectionType = 'wifi'
            break
          case 'cellular':
            connectionType = 'cellular'
            break
          case 'ethernet':
            connectionType = 'ethernet'
            break
          default:
            connectionType = 'none'
        }
      } else {
        // Fallback: assume WiFi for fast connections, cellular for slower
        connectionType = ['4g', '3g', '2g', 'slow-2g'].includes(effectiveType) ? 'cellular' : 'wifi'
      }
    }

    // Test actual connectivity with a lightweight external request
    try {
      // Use a reliable external service for connectivity test
      // Create AbortController for timeout (better browser compatibility)
      const controller = new AbortController()
      const timeoutId = setTimeout(() => controller.abort(), 5000)
      
      const response = await fetch('https://www.google.com/favicon.ico', { 
        method: 'HEAD',
        cache: 'no-cache',
        signal: controller.signal,
        mode: 'no-cors' // Prevent CORS issues
      })
      
      clearTimeout(timeoutId)
      
      // For no-cors mode, we just check if the request completed
      const isReallyConnected = true // If we get here, we have connectivity
      
      setWiFiStatus({
        isConnected: isReallyConnected,
        networkName: connectionType === 'wifi' ? getNetworkName() : undefined,
        signalStrength: getSignalStrength(),
        connectionType: isReallyConnected ? connectionType : 'none',
        isOnline: isReallyConnected
      })
    } catch (error) {
      // If external test fails, fall back to navigator.onLine
      setWiFiStatus({
        isConnected: isOnline,
        networkName: connectionType === 'wifi' ? getNetworkName() : undefined,
        signalStrength: getSignalStrength(),
        connectionType: isOnline ? connectionType : 'none',
        isOnline: isOnline
      })
    }
  }

  const getNetworkName = (): string | undefined => {
    // In a real app, you might get this from device APIs
    // For web apps, this is limited due to security restrictions
    if ('connection' in navigator) {
      return 'WiFi Network' // Generic name since browser can't access SSID
    }
    return undefined
  }

  const getSignalStrength = (): number | undefined => {
    // In a real app with device access, you could get actual signal strength
    // For web, this is not available due to privacy/security restrictions
    if ('connection' in navigator) {
      const connection = (navigator as any).connection
      if (connection.downlink) {
        // Estimate signal strength based on connection speed
        const speed = connection.downlink // Mbps
        if (speed > 10) return 4 // Excellent
        if (speed > 5) return 3  // Good
        if (speed > 1) return 2  // Fair
        return 1 // Poor
      }
    }
    return undefined
  }

  return wifiStatus
}