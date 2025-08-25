"use client"

import { useState, useEffect } from 'react'
import { biometricPlugin } from '@/lib/biometric-plugin'
import type {
  BiometricAuthenticationStatus,
  BiometricCredentials,
  VerifyIdentityOptions
} from '@/lib/biometric-plugin'

interface BiometricCapabilities {
  isAvailable: boolean
  supportedTypes: string[]
  hasEnrolledCredentials: boolean
}

interface BiometricAuthResult {
  success: boolean
  error?: string
  cancelled?: boolean
}

/**
 * Hook for biometric authentication (Face ID, Touch ID, Fingerprint)
 * Works with both web and mobile platforms
 */
export function useBiometricAuth() {
  const [capabilities, setCapabilities] = useState<BiometricCapabilities>({
    isAvailable: false,
    supportedTypes: [],
    hasEnrolledCredentials: false
  })
  const [isLoading, setIsLoading] = useState(false)

  useEffect(() => {
    // Only check capabilities if we're in a browser environment
    if (typeof window !== 'undefined') {
      checkBiometricCapabilities()
    }
  }, [])

  const checkBiometricCapabilities = async () => {
    try {
      // First try mobile biometrics (will fail gracefully on web)
      await checkMobileBiometrics()
      
      // If mobile biometrics not available, try web biometrics
      if (!capabilities.isAvailable && typeof window !== 'undefined') {
        await checkWebBiometrics()
      }
    } catch (error) {
      console.warn('Biometric capability check failed:', error)
      setCapabilities({
        isAvailable: false,
        supportedTypes: [],
        hasEnrolledCredentials: false
      })
    }
  }

  const checkMobileBiometrics = async () => {
    try {
      const result = await biometricPlugin.isAvailable()
      
      if (result.isAvailable) {
        const hasCredentials = await biometricPlugin.getCredentials({ server: 'kswifi.app' })
          .then(() => true)
          .catch(() => false)

        setCapabilities({
          isAvailable: result.isAvailable,
          supportedTypes: result.biometryType ? [result.biometryType] : [],
          hasEnrolledCredentials: hasCredentials
        })
      } else {
        setCapabilities({
          isAvailable: false,
          supportedTypes: [],
          hasEnrolledCredentials: false
        })
      }
    } catch (error) {
      console.warn('Mobile biometric check failed:', error)
      setCapabilities({
        isAvailable: false,
        supportedTypes: [],
        hasEnrolledCredentials: false
      })
    }
  }

  const checkWebBiometrics = async () => {
    try {
      // Check for WebAuthn support
      if (window.PublicKeyCredential) {
        const available = await PublicKeyCredential.isUserVerifyingPlatformAuthenticatorAvailable()
        
        setCapabilities({
          isAvailable: available,
          supportedTypes: available ? ['platform'] : [],
          hasEnrolledCredentials: false // Cannot check on web without attempting auth
        })
      } else {
        setCapabilities({
          isAvailable: false,
          supportedTypes: [],
          hasEnrolledCredentials: false
        })
      }
    } catch (error) {
      console.warn('Web biometric check failed:', error)
      setCapabilities({
        isAvailable: false,
        supportedTypes: [],
        hasEnrolledCredentials: false
      })
    }
  }

  const authenticateWithBiometrics = async (
    reason: string = "Authenticate to access your account"
  ): Promise<BiometricAuthResult> => {
    if (!capabilities.isAvailable) {
      return {
        success: false,
        error: "Biometric authentication is not available on this device"
      }
    }

    setIsLoading(true)

    try {
      // Try mobile authentication first
      try {
        return await authenticateMobile(reason)
      } catch (mobileError) {
        // If mobile auth fails and we're on web, try web auth
        if (typeof window !== 'undefined' && window.PublicKeyCredential) {
          return await authenticateWeb(reason)
        }
        throw mobileError
      }
    } catch (error) {
      console.error('Biometric authentication error:', error)
      return {
        success: false,
        error: error instanceof Error ? error.message : 'Authentication failed'
      }
    } finally {
      setIsLoading(false)
    }
  }

  const authenticateMobile = async (reason: string): Promise<BiometricAuthResult> => {
    try {
      await biometricPlugin.verifyIdentity({
        reason,
        title: "KSWiFi Authentication",
        subtitle: "Use your biometric to sign in",
        description: "Place your finger on the sensor or look at the camera"
      })

      return {
        success: true
      }
    } catch (error: any) {
      if (error.code === 'userCancel' || error.message?.includes('cancel')) {
        return {
          success: false,
          cancelled: true,
          error: 'Authentication was cancelled'
        }
      }
      
      return {
        success: false,
        error: error.message || 'Biometric authentication failed'
      }
    }
  }

  const authenticateWeb = async (reason: string): Promise<BiometricAuthResult> => {
    try {
      // Create a credential request for WebAuthn
      const credential = await navigator.credentials.create({
        publicKey: {
          challenge: new TextEncoder().encode('kswifi-auth-challenge'),
          rp: {
            name: "KSWiFi",
            id: window.location.hostname
          },
          user: {
            id: new TextEncoder().encode('user-id'),
            name: 'user@kswifi.app',
            displayName: 'KSWiFi User'
          },
          pubKeyCredParams: [{
            type: 'public-key',
            alg: -7 // ES256
          }],
          authenticatorSelection: {
            authenticatorAttachment: 'platform',
            userVerification: 'required'
          },
          timeout: 60000,
          attestation: 'direct'
        }
      })

      if (credential) {
        return { success: true }
      } else {
        return {
          success: false,
          error: 'No credential created'
        }
      }
    } catch (error: any) {
      if (error.name === 'NotAllowedError') {
        return {
          success: false,
          cancelled: true,
          error: 'Authentication was cancelled or failed'
        }
      }
      
      return {
        success: false,
        error: error.message || 'Web authentication failed'
      }
    }
  }

  const saveBiometricCredentials = async (username: string, password: string): Promise<boolean> => {
    if (!capabilities.isAvailable) return false

    try {
      await biometricPlugin.setCredentials({
        username,
        password,
        server: 'kswifi.app'
      })
      
      return true
    } catch (error) {
      console.error('Failed to save biometric credentials:', error)
      return false
    }
  }

  const getBiometricCredentials = async (): Promise<{ username: string; password: string } | null> => {
    if (!capabilities.isAvailable) return null

    try {
      const credentials = await biometricPlugin.getCredentials({
        server: 'kswifi.app'
      })
      
      return {
        username: credentials.username,
        password: credentials.password
      }
    } catch (error) {
      console.error('Failed to get biometric credentials:', error)
      return null
    }
  }

  const deleteBiometricCredentials = async (): Promise<boolean> => {
    try {
      await biometricPlugin.deleteCredentials({
        server: 'kswifi.app'
      })
      
      return true
    } catch (error) {
      console.error('Failed to delete biometric credentials:', error)
      return false
    }
  }

  const getBiometricTypeIcon = () => {
    if (!capabilities.isAvailable) return '🔒'
    
    const type = capabilities.supportedTypes[0]
    switch (type) {
      case 'face':
      case 'faceId':
        return '👤'
      case 'fingerprint':
      case 'touchId':
        return '👆'
      case 'platform':
        return '🔐'
      default:
        return '🔒'
    }
  }

  const getBiometricTypeName = () => {
    if (!capabilities.isAvailable) return 'Biometric'
    
    const type = capabilities.supportedTypes[0]
    switch (type) {
      case 'face':
      case 'faceId':
        return 'Face ID'
      case 'fingerprint':
      case 'touchId':
        return 'Touch ID'
      case 'platform':
        return 'Biometric'
      default:
        return 'Biometric'
    }
  }

  return {
    capabilities,
    isLoading,
    authenticateWithBiometrics,
    saveBiometricCredentials,
    getBiometricCredentials,
    deleteBiometricCredentials,
    getBiometricTypeIcon,
    getBiometricTypeName,
    checkBiometricCapabilities
  }
}