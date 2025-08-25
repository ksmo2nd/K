"use client"

// Safe wrapper for Capacitor Native Biometric plugin
// This module handles dynamic imports and provides type safety

interface BiometricAuthenticationStatus {
  isAvailable: boolean
  biometryType?: string
  strongBiometryIsAvailable?: boolean
}

interface BiometricCredentials {
  username: string
  password: string
}

interface SetCredentialsOptions {
  username: string
  password: string
  server: string
}

interface GetCredentialsOptions {
  server: string
}

interface DeleteCredentialsOptions {
  server: string
}

interface VerifyIdentityOptions {
  reason: string
  title?: string
  subtitle?: string
  description?: string
  negativeButtonText?: string
  maxAttempts?: number
}

// Safe plugin interface
interface NativeBiometricPlugin {
  isAvailable(): Promise<BiometricAuthenticationStatus>
  verifyIdentity(options: VerifyIdentityOptions): Promise<void>
  setCredentials(options: SetCredentialsOptions): Promise<void>
  getCredentials(options: GetCredentialsOptions): Promise<BiometricCredentials>
  deleteCredentials(options: DeleteCredentialsOptions): Promise<void>
}

class BiometricPluginWrapper {
  private plugin: NativeBiometricPlugin | null = null
  private isInitialized = false

  private async initializePlugin(): Promise<NativeBiometricPlugin | null> {
    if (this.isInitialized) {
      return this.plugin
    }

    try {
      // Only attempt to load on mobile platforms
      if (typeof window !== 'undefined' && 
          (window as any).Capacitor?.isNativePlatform?.()) {
        
        // Use eval to prevent TypeScript from analyzing this import at compile time
        const pluginModule = await eval('import("@capawesome/capacitor-native-biometric")')
        this.plugin = pluginModule.NativeBiometric
        this.isInitialized = true
        return this.plugin
      } else {
        console.log('BiometricPlugin: Not on mobile platform, biometrics not available')
        this.isInitialized = true
        return null
      }
    } catch (error) {
      console.warn('BiometricPlugin: Failed to load native biometric plugin:', error)
      this.isInitialized = true
      return null
    }
  }

  async isAvailable(): Promise<BiometricAuthenticationStatus> {
    const plugin = await this.initializePlugin()
    if (!plugin) {
      return { isAvailable: false }
    }
    return plugin.isAvailable()
  }

  async verifyIdentity(options: VerifyIdentityOptions): Promise<void> {
    const plugin = await this.initializePlugin()
    if (!plugin) {
      throw new Error('Biometric authentication not available on this platform')
    }
    return plugin.verifyIdentity(options)
  }

  async setCredentials(options: SetCredentialsOptions): Promise<void> {
    const plugin = await this.initializePlugin()
    if (!plugin) {
      throw new Error('Biometric credential storage not available on this platform')
    }
    return plugin.setCredentials(options)
  }

  async getCredentials(options: GetCredentialsOptions): Promise<BiometricCredentials> {
    const plugin = await this.initializePlugin()
    if (!plugin) {
      throw new Error('Biometric credential retrieval not available on this platform')
    }
    return plugin.getCredentials(options)
  }

  async deleteCredentials(options: DeleteCredentialsOptions): Promise<void> {
    const plugin = await this.initializePlugin()
    if (!plugin) {
      throw new Error('Biometric credential deletion not available on this platform')
    }
    return plugin.deleteCredentials(options)
  }
}

// Export a singleton instance
export const biometricPlugin = new BiometricPluginWrapper()

// Export types for use in other files
export type {
  BiometricAuthenticationStatus,
  BiometricCredentials,
  SetCredentialsOptions,
  GetCredentialsOptions,
  DeleteCredentialsOptions,
  VerifyIdentityOptions
}