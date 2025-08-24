"use client"

import { useState } from 'react'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { Label } from '@/components/ui/label'
import { Card, CardHeader, CardTitle, CardContent, CardFooter } from '@/components/ui/card'
import { useAuth } from '@/lib/auth-context'
import { Eye, EyeOff, Loader2, Check, X, CheckCircle } from 'lucide-react'

interface PasswordUpdateFormProps {
  onSuccess?: () => void
}

export function PasswordUpdateForm({ onSuccess }: PasswordUpdateFormProps) {
  const { updatePassword } = useAuth()
  const [formData, setFormData] = useState({
    password: '',
    confirmPassword: ''
  })
  const [showPassword, setShowPassword] = useState(false)
  const [showConfirmPassword, setShowConfirmPassword] = useState(false)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [success, setSuccess] = useState(false)

  // Password validation
  const passwordRequirements = {
    length: formData.password.length >= 8,
    uppercase: /[A-Z]/.test(formData.password),
    lowercase: /[a-z]/.test(formData.password),
    number: /\d/.test(formData.password),
    special: /[!@#$%^&*(),.?":{}|<>]/.test(formData.password)
  }

  const isPasswordValid = Object.values(passwordRequirements).every(Boolean)
  const doPasswordsMatch = formData.password === formData.confirmPassword && formData.confirmPassword.length > 0

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    setLoading(true)
    setError(null)

    // Validation
    if (!isPasswordValid) {
      setError('Password does not meet requirements')
      setLoading(false)
      return
    }

    if (!doPasswordsMatch) {
      setError('Passwords do not match')
      setLoading(false)
      return
    }

    try {
      const { data, error } = await updatePassword(formData.password)
      
      if (error) {
        throw error
      }

      setSuccess(true)
      setTimeout(() => {
        onSuccess?.()
      }, 2000)
    } catch (err: any) {
      console.error('Password update error:', err)
      setError(err.message || 'Failed to update password. Please try again.')
    } finally {
      setLoading(false)
    }
  }

  const handleInputChange = (field: string, value: string) => {
    setFormData(prev => ({ ...prev, [field]: value }))
    setError(null) // Clear error when user starts typing
  }

  const RequirementItem = ({ met, text }: { met: boolean; text: string }) => (
    <div className={`flex items-center text-xs ${met ? 'text-green-600' : 'text-gray-500'}`}>
      {met ? <Check className="h-3 w-3 mr-1" /> : <X className="h-3 w-3 mr-1" />}
      {text}
    </div>
  )

  if (success) {
    return (
      <Card className="w-full max-w-md mx-auto">
        <CardHeader className="text-center">
          <div className="mx-auto mb-4 flex h-12 w-12 items-center justify-center rounded-full bg-green-100">
            <CheckCircle className="h-6 w-6 text-green-600" />
          </div>
          <CardTitle className="text-2xl font-bold">Password Updated</CardTitle>
          <p className="text-muted-foreground">
            Your password has been successfully updated. You will be redirected shortly.
          </p>
        </CardHeader>
      </Card>
    )
  }

  return (
    <Card className="w-full max-w-md mx-auto">
      <CardHeader className="text-center">
        <CardTitle className="text-2xl font-bold">Update Password</CardTitle>
        <p className="text-muted-foreground">Enter your new password</p>
      </CardHeader>
      
      <form onSubmit={handleSubmit}>
        <CardContent className="space-y-4">
          {error && (
            <div className="p-3 text-sm text-red-600 bg-red-50 border border-red-200 rounded-md">
              {error}
            </div>
          )}

          <div className="space-y-2">
            <Label htmlFor="password">New Password</Label>
            <div className="relative">
              <Input
                id="password"
                type={showPassword ? 'text' : 'password'}
                placeholder="Enter your new password"
                value={formData.password}
                onChange={(e) => handleInputChange('password', e.target.value)}
                required
                disabled={loading}
                className="pr-10"
              />
              <Button
                type="button"
                variant="ghost"
                size="sm"
                className="absolute right-0 top-0 h-full px-3 py-2 hover:bg-transparent"
                onClick={() => setShowPassword(!showPassword)}
                disabled={loading}
              >
                {showPassword ? (
                  <EyeOff className="h-4 w-4" />
                ) : (
                  <Eye className="h-4 w-4" />
                )}
              </Button>
            </div>
            
            {formData.password && (
              <div className="space-y-1 p-2 bg-gray-50 rounded">
                <RequirementItem met={passwordRequirements.length} text="At least 8 characters" />
                <RequirementItem met={passwordRequirements.uppercase} text="One uppercase letter" />
                <RequirementItem met={passwordRequirements.lowercase} text="One lowercase letter" />
                <RequirementItem met={passwordRequirements.number} text="One number" />
                <RequirementItem met={passwordRequirements.special} text="One special character" />
              </div>
            )}
          </div>

          <div className="space-y-2">
            <Label htmlFor="confirmPassword">Confirm New Password</Label>
            <div className="relative">
              <Input
                id="confirmPassword"
                type={showConfirmPassword ? 'text' : 'password'}
                placeholder="Confirm your new password"
                value={formData.confirmPassword}
                onChange={(e) => handleInputChange('confirmPassword', e.target.value)}
                required
                disabled={loading}
                className="pr-10"
              />
              <Button
                type="button"
                variant="ghost"
                size="sm"
                className="absolute right-0 top-0 h-full px-3 py-2 hover:bg-transparent"
                onClick={() => setShowConfirmPassword(!showConfirmPassword)}
                disabled={loading}
              >
                {showConfirmPassword ? (
                  <EyeOff className="h-4 w-4" />
                ) : (
                  <Eye className="h-4 w-4" />
                )}
              </Button>
            </div>
            
            {formData.confirmPassword && (
              <div className={`text-xs ${doPasswordsMatch ? 'text-green-600' : 'text-red-600'}`}>
                {doPasswordsMatch ? (
                  <div className="flex items-center">
                    <Check className="h-3 w-3 mr-1" />
                    Passwords match
                  </div>
                ) : (
                  <div className="flex items-center">
                    <X className="h-3 w-3 mr-1" />
                    Passwords do not match
                  </div>
                )}
              </div>
            )}
          </div>
        </CardContent>

        <CardFooter>
          <Button 
            type="submit" 
            className="w-full" 
            disabled={loading || !isPasswordValid || !doPasswordsMatch}
          >
            {loading ? (
              <>
                <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                Updating Password...
              </>
            ) : (
              'Update Password'
            )}
          </Button>
        </CardFooter>
      </form>
    </Card>
  )
}