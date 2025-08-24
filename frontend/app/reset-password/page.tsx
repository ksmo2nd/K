"use client"

import { useEffect, useState, Suspense } from 'react'
import { useRouter } from 'next/navigation'
import { PasswordUpdateForm } from '@/components/auth/password-update-form'
import { AuthProvider } from '@/lib/auth-context'
import { supabase } from '@/lib/supabase'

function ResetPasswordContent() {
  const router = useRouter()
  const [isValidSession, setIsValidSession] = useState(false)
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    // Handle the password reset flow
    const handlePasswordReset = async () => {
      try {
        // Get the hash fragment from URL
        const hashFragment = window.location.hash.substring(1)
        const params = new URLSearchParams(hashFragment)
        
        const accessToken = params.get('access_token')
        const refreshToken = params.get('refresh_token')
        const type = params.get('type')

        if (type === 'recovery' && accessToken && refreshToken) {
          // Set the session with the tokens from the URL
          const { data, error } = await supabase.auth.setSession({
            access_token: accessToken,
            refresh_token: refreshToken
          })

          if (error) {
            console.error('Error setting session:', error)
            router.push('/?error=invalid_reset_link')
          } else {
            setIsValidSession(true)
          }
        } else {
          // No valid reset parameters
          router.push('/?error=invalid_reset_link')
        }
      } catch (error) {
        console.error('Password reset error:', error)
        router.push('/?error=reset_error')
      } finally {
        setLoading(false)
      }
    }

    handlePasswordReset()
  }, [router])

  const handleSuccess = () => {
    router.push('/?message=password_updated')
  }

  if (loading) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-gradient-to-br from-blue-50 to-indigo-100">
        <div className="text-center">
          <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600 mx-auto mb-4"></div>
          <p className="text-gray-600">Verifying reset link...</p>
        </div>
      </div>
    )
  }

  if (!isValidSession) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-gradient-to-br from-blue-50 to-indigo-100">
        <div className="text-center">
          <h1 className="text-2xl font-bold text-gray-900 mb-2">Invalid Reset Link</h1>
          <p className="text-gray-600 mb-4">This password reset link is invalid or has expired.</p>
          <button
            onClick={() => router.push('/')}
            className="bg-blue-600 text-white px-4 py-2 rounded hover:bg-blue-700"
          >
            Go Back
          </button>
        </div>
      </div>
    )
  }

  return (
    <div className="min-h-screen flex items-center justify-center bg-gradient-to-br from-blue-50 to-indigo-100 p-4">
      <PasswordUpdateForm onSuccess={handleSuccess} />
    </div>
  )
}

export default function ResetPasswordPage() {
  return (
    <AuthProvider>
      <Suspense fallback={
        <div className="min-h-screen flex items-center justify-center bg-gradient-to-br from-blue-50 to-indigo-100">
          <div className="text-center">
            <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600 mx-auto mb-4"></div>
            <p className="text-gray-600">Loading...</p>
          </div>
        </div>
      }>
        <ResetPasswordContent />
      </Suspense>
    </AuthProvider>
  )
}