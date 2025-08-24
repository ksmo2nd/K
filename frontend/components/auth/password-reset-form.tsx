"use client"

import { useState } from 'react'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { Label } from '@/components/ui/label'
import { Card, CardHeader, CardTitle, CardContent, CardFooter } from '@/components/ui/card'
import { useAuth } from '@/lib/auth-context'
import { Loader2, ArrowLeft, CheckCircle } from 'lucide-react'

interface PasswordResetFormProps {
  onBack?: () => void
}

export function PasswordResetForm({ onBack }: PasswordResetFormProps) {
  const { resetPassword } = useAuth()
  const [email, setEmail] = useState('')
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [success, setSuccess] = useState(false)

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    setLoading(true)
    setError(null)

    try {
      const { data, error } = await resetPassword(email)
      
      if (error) {
        throw error
      }

      setSuccess(true)
    } catch (err: any) {
      console.error('Password reset error:', err)
      setError(err.message || 'Failed to send reset email. Please try again.')
    } finally {
      setLoading(false)
    }
  }

  if (success) {
    return (
      <Card className="w-full max-w-md mx-auto">
        <CardHeader className="text-center">
          <div className="mx-auto mb-4 flex h-12 w-12 items-center justify-center rounded-full bg-green-100">
            <CheckCircle className="h-6 w-6 text-green-600" />
          </div>
          <CardTitle className="text-2xl font-bold">Check Your Email</CardTitle>
          <p className="text-muted-foreground">
            We've sent a password reset link to <strong>{email}</strong>
          </p>
        </CardHeader>
        
        <CardContent className="text-center text-sm text-muted-foreground">
          <p>
            Click the link in the email to reset your password. 
            If you don't see the email, check your spam folder.
          </p>
        </CardContent>

        <CardFooter className="flex flex-col space-y-4">
          <Button 
            variant="outline" 
            onClick={() => {
              setSuccess(false)
              setEmail('')
              setError(null)
            }}
            className="w-full"
          >
            Send Another Email
          </Button>

          <Button
            variant="link"
            onClick={onBack}
            className="w-full"
          >
            <ArrowLeft className="mr-2 h-4 w-4" />
            Back to Sign In
          </Button>
        </CardFooter>
      </Card>
    )
  }

  return (
    <Card className="w-full max-w-md mx-auto">
      <CardHeader className="text-center">
        <CardTitle className="text-2xl font-bold">Reset Password</CardTitle>
        <p className="text-muted-foreground">
          Enter your email address and we'll send you a link to reset your password
        </p>
      </CardHeader>
      
      <form onSubmit={handleSubmit}>
        <CardContent className="space-y-4">
          {error && (
            <div className="p-3 text-sm text-red-600 bg-red-50 border border-red-200 rounded-md">
              {error}
            </div>
          )}

          <div className="space-y-2">
            <Label htmlFor="email">Email Address</Label>
            <Input
              id="email"
              type="email"
              placeholder="Enter your email address"
              value={email}
              onChange={(e) => {
                setEmail(e.target.value)
                setError(null)
              }}
              required
              disabled={loading}
            />
          </div>
        </CardContent>

        <CardFooter className="flex flex-col space-y-4">
          <Button 
            type="submit" 
            className="w-full" 
            disabled={loading || !email}
          >
            {loading ? (
              <>
                <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                Sending Reset Link...
              </>
            ) : (
              'Send Reset Link'
            )}
          </Button>

          <Button
            type="button"
            variant="link"
            onClick={onBack}
            disabled={loading}
            className="w-full"
          >
            <ArrowLeft className="mr-2 h-4 w-4" />
            Back to Sign In
          </Button>
        </CardFooter>
      </form>
    </Card>
  )
}