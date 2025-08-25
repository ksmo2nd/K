// Type declarations for @capawesome/capacitor-native-biometric
// This allows TypeScript to compile without the actual package being installed
// These types are only used for compilation - the actual plugin is loaded dynamically on mobile

declare module '@capawesome/capacitor-native-biometric' {
  /**
   * Biometric authentication availability status
   */
  export interface BiometricAuthenticationStatus {
    isAvailable: boolean
    biometryType?: 'face' | 'faceId' | 'fingerprint' | 'touchId' | 'none' | string
    strongBiometryIsAvailable?: boolean
  }

  /**
   * Stored biometric credentials
   */
  export interface BiometricCredentials {
    username: string
    password: string
  }

  /**
   * Options for storing credentials
   */
  export interface SetCredentialsOptions {
    username: string
    password: string
    server: string
  }

  /**
   * Options for retrieving credentials
   */
  export interface GetCredentialsOptions {
    server: string
  }

  /**
   * Options for deleting credentials
   */
  export interface DeleteCredentialsOptions {
    server: string
  }

  /**
   * Options for biometric verification
   */
  export interface VerifyIdentityOptions {
    reason: string
    title?: string
    subtitle?: string
    description?: string
    negativeButtonText?: string
    maxAttempts?: number
  }

  /**
   * Biometric authentication error
   */
  export interface BiometricAuthenticationError extends Error {
    code: 'userCancel' | 'userFallback' | 'systemCancel' | 'passcodeNotSet' | 'biometryNotAvailable' | 'biometryNotEnrolled' | 'biometryLockout' | string
    message: string
  }

  /**
   * Native Biometric plugin interface
   * Note: This is only available on mobile platforms with Capacitor
   */
  export class NativeBiometric {
    /**
     * Check if biometric authentication is available
     */
    static isAvailable(): Promise<BiometricAuthenticationStatus>
    
    /**
     * Verify user identity using biometrics
     */
    static verifyIdentity(options: VerifyIdentityOptions): Promise<void>
    
    /**
     * Store credentials securely with biometric protection
     */
    static setCredentials(options: SetCredentialsOptions): Promise<void>
    
    /**
     * Retrieve stored credentials after biometric verification
     */
    static getCredentials(options: GetCredentialsOptions): Promise<BiometricCredentials>
    
    /**
     * Delete stored credentials
     */
    static deleteCredentials(options: DeleteCredentialsOptions): Promise<void>
  }

  // Default export for compatibility
  export { NativeBiometric as default }
}

// Global type augmentation for Capacitor
declare global {
  interface Window {
    /**
     * Capacitor runtime - only available in mobile apps
     */
    Capacitor?: {
      isNativePlatform?: () => boolean
      getPlatform?: () => 'ios' | 'android' | 'web' | string
      isPluginAvailable?: (name: string) => boolean
      convertFileSrc?: (filePath: string) => string
    }
  }
}

// Ensure this is treated as a module
export {}