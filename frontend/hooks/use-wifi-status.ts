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

    // Simplified: If online, assume connected
    // The complex detection was causing issues
    let connectionType: 'wifi' | 'cellular' | 'ethernet' | 'none' = 'wifi' // Default to wifi
    let networkName = 'Connected Network' // Generic name since browser can't access SSID

    // Try to determine connection type using Network Information API (if available)
    if ('connection' in navigator) {
      const connection = (navigator as any).connection
      
      if (connection.type) {
        switch (connection.type) {
          case 'wifi':
            connectionType = 'wifi'
            networkName = 'WiFi Network'
            break
          case 'cellular':
            connectionType = 'cellular'
            networkName = 'Cellular Network'
            break
          case 'ethernet':
            connectionType = 'ethernet'
            networkName = 'Ethernet Connection'
            break
          default:
            connectionType = 'wifi' // Default to wifi
            networkName = 'Connected Network'
        }
      } else {
        // Fallback: assume WiFi for most web connections
        connectionType = 'wifi'
        networkName = 'WiFi Network'
      }
    }

    // Always set as connected if online (simplified approach)
    setWiFiStatus({
      isConnected: true, // If navigator.onLine is true, we're connected
      networkName: networkName,
      signalStrength: getSignalStrength(),
      connectionType: connectionType,
      isOnline: true
    })
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