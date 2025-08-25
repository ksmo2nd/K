"use client"

import { useState, useEffect } from 'react'

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
      // Check if running on mobile (Capacitor)
      if (typeof window !== 'undefined' && (window as any).Capacitor) {
        await checkMobileBiometrics()
      } else {
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
      // Check if the plugin is available (only on mobile)
      if (typeof window !== 'undefined' && (window as any).Capacitor?.isNativePlatform?.()) {
        // Dynamically import only if we're actually on a mobile platform
        const { NativeBiometric } = await import('@capawesome/capacitor-native-biometric')
        
        const result = await NativeBiometric.isAvailable()
        const hasCredentials = await NativeBiometric.getCredentials({ server: 'kswifi.app' })
          .then(() => true)
          .catch(() => false)

        setCapabilities({
          isAvailable: result.isAvailable,
          supportedTypes: result.biometryType ? [result.biometryType] : [],
          hasEnrolledCredentials: hasCredentials
        })
      } else {
        // Not on mobile platform, biometrics not available
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
      if (typeof window !== 'undefined' && (window as any).Capacitor) {
        return await authenticateMobile(reason)
      } else {
        return await authenticateWeb(reason)
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
      // Only import if we're on a mobile platform
      if (typeof window !== 'undefined' && (window as any).Capacitor?.isNativePlatform?.()) {
        const { NativeBiometric } = await import('@capawesome/capacitor-native-biometric')
        
        const result = await NativeBiometric.verifyIdentity({
          reason,
          title: "KSWiFi Authentication",
          subtitle: "Use your biometric to sign in",
          description: "Place your finger on the sensor or look at the camera"
        })

        return {
          success: true
        }
      } else {
        return {
          success: false,
          error: 'Mobile biometric authentication not available on this platform'
        }
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
      if (typeof window !== 'undefined' && (window as any).Capacitor?.isNativePlatform?.()) {
        const { NativeBiometric } = await import('@capawesome/capacitor-native-biometric')
        
        await NativeBiometric.setCredentials({
          username,
          password,
          server: 'kswifi.app'
        })
        
        return true
      }
      
      // For web, we'd typically use a more secure storage method
      // This is a simplified implementation
      return false
    } catch (error) {
      console.error('Failed to save biometric credentials:', error)
      return false
    }
  }

  const getBiometricCredentials = async (): Promise<{ username: string; password: string } | null> => {
    if (!capabilities.isAvailable) return null

    try {
      if (typeof window !== 'undefined' && (window as any).Capacitor?.isNativePlatform?.()) {
        const { NativeBiometric } = await import('@capawesome/capacitor-native-biometric')
        
        const credentials = await NativeBiometric.getCredentials({
          server: 'kswifi.app'
        })
        
        return {
          username: credentials.username,
          password: credentials.password
        }
      }
      
      return null
    } catch (error) {
      console.error('Failed to get biometric credentials:', error)
      return null
    }
  }

  const deleteBiometricCredentials = async (): Promise<boolean> => {
    try {
      if (typeof window !== 'undefined' && (window as any).Capacitor?.isNativePlatform?.()) {
        const { NativeBiometric } = await import('@capawesome/capacitor-native-biometric')
        
        await NativeBiometric.deleteCredentials({
          server: 'kswifi.app'
        })
        
        return true
      }
      
      return false
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