"use client"

import { useState } from 'react'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { Label } from '@/components/ui/label'
import { Card, CardHeader, CardTitle, CardContent, CardFooter } from '@/components/ui/card'
import { useAuth } from '@/lib/auth-context'
import { Eye, EyeOff, Loader2, Check, X } from 'lucide-react'

interface SignUpFormProps {
  onSuccess?: () => void
  onSwitchToSignIn?: () => void
}

export function SignUpForm({ onSuccess, onSwitchToSignIn }: SignUpFormProps) {
  const { signUp } = useAuth()
  const [formData, setFormData] = useState({
    first_name: '',
    last_name: '',
    email: '',
    phone_number: '',
    password: '',
    confirmPassword: ''
  })
  const [showPassword, setShowPassword] = useState(false)
  const [showConfirmPassword, setShowConfirmPassword] = useState(false)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)

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
      const { data, error } = await signUp(formData.email, formData.password, {
        first_name: formData.first_name,
        last_name: formData.last_name,
        phone_number: formData.phone_number || undefined
      })
      
      if (error) {
        throw error
      }

      if (data?.user) {
        onSuccess?.()
      }
    } catch (err: any) {
      console.error('Sign up error:', err)
      setError(err.message || 'Failed to create account. Please try again.')
    } finally {
      setLoading(false)
    }
  }

  const handleInputChange = (field: string, value: string) => {
    setFormData(prev => ({ ...prev, [field]: value }))
    setError(null) // Clear error when user starts typing
  }

  const RequirementItem = ({ met, text }: { met: boolean; text: string }) => (
    <div className={`flex items-center text-xs ${met ? 'text-primary' : 'text-muted-foreground'}`}>
      {met ? <Check className="h-3 w-3 mr-1" /> : <X className="h-3 w-3 mr-1" />}
      {text}
    </div>
  )

  return (
    <Card className="w-full max-w-md mx-auto bg-card border-border">
      <CardHeader className="text-center">
        <CardTitle className="text-2xl font-bold text-foreground">Create Account</CardTitle>
        <p className="text-muted-foreground">Sign up for your KSWiFi account</p>
      </CardHeader>
      
      <form onSubmit={handleSubmit}>
        <CardContent className="space-y-4">
          {error && (
            <div className="p-3 text-sm text-red-400 bg-red-900/20 border border-red-800 rounded-md">
              {error}
            </div>
          )}

          <div className="grid grid-cols-2 gap-4">
            <div className="space-y-2">
              <Label htmlFor="first_name" className="text-foreground">First Name</Label>
              <Input
                id="first_name"
                type="text"
                placeholder="First name"
                value={formData.first_name}
                onChange={(e) => handleInputChange('first_name', e.target.value)}
                required
                disabled={loading}
                className="bg-input border-border text-foreground placeholder:text-muted-foreground focus:ring-primary"
              />
            </div>

            <div className="space-y-2">
              <Label htmlFor="last_name" className="text-foreground">Last Name</Label>
              <Input
                id="last_name"
                type="text"
                placeholder="Last name"
                value={formData.last_name}
                onChange={(e) => handleInputChange('last_name', e.target.value)}
                required
                disabled={loading}
                className="bg-input border-border text-foreground placeholder:text-muted-foreground focus:ring-primary"
              />
            </div>
          </div>

          <div className="space-y-2">
            <Label htmlFor="email" className="text-foreground">Email</Label>
            <Input
              id="email"
              type="email"
              placeholder="Enter your email"
              value={formData.email}
              onChange={(e) => handleInputChange('email', e.target.value)}
              required
              disabled={loading}
              className="bg-input border-border text-foreground placeholder:text-muted-foreground focus:ring-primary"
            />
          </div>

          <div className="space-y-2">
            <Label htmlFor="phone_number" className="text-foreground">Phone Number (Optional)</Label>
            <Input
              id="phone_number"
              type="tel"
              placeholder="Enter your phone number"
              value={formData.phone_number}
              onChange={(e) => handleInputChange('phone_number', e.target.value)}
              disabled={loading}
              className="bg-input border-border text-foreground placeholder:text-muted-foreground focus:ring-primary"
            />
          </div>

          <div className="space-y-2">
            <Label htmlFor="password" className="text-foreground">Password</Label>
            <div className="relative">
              <Input
                id="password"
                type={showPassword ? 'text' : 'password'}
                placeholder="Create a password"
                value={formData.password}
                onChange={(e) => handleInputChange('password', e.target.value)}
                required
                disabled={loading}
                className="pr-10 bg-input border-border text-foreground placeholder:text-muted-foreground focus:ring-primary"
              />
              <Button
                type="button"
                variant="ghost"
                size="sm"
                className="absolute right-0 top-0 h-full px-3 py-2 hover:bg-muted text-muted-foreground hover:text-foreground"
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
              <div className="space-y-1 p-2 bg-muted/20 border border-border rounded">
                <RequirementItem met={passwordRequirements.length} text="At least 8 characters" />
                <RequirementItem met={passwordRequirements.uppercase} text="One uppercase letter" />
                <RequirementItem met={passwordRequirements.lowercase} text="One lowercase letter" />
                <RequirementItem met={passwordRequirements.number} text="One number" />
                <RequirementItem met={passwordRequirements.special} text="One special character" />
              </div>
            )}
          </div>

          <div className="space-y-2">
            <Label htmlFor="confirmPassword" className="text-foreground">Confirm Password</Label>
            <div className="relative">
              <Input
                id="confirmPassword"
                type={showConfirmPassword ? 'text' : 'password'}
                placeholder="Confirm your password"
                value={formData.confirmPassword}
                onChange={(e) => handleInputChange('confirmPassword', e.target.value)}
                required
                disabled={loading}
                className="pr-10 bg-input border-border text-foreground placeholder:text-muted-foreground focus:ring-primary"
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
              <div className={`text-xs ${doPasswordsMatch ? 'text-primary' : 'text-red-400'}`}>
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

        <CardFooter className="flex flex-col space-y-4">
          <Button 
            type="submit" 
            className="w-full bg-primary text-primary-foreground hover:bg-primary/90 focus:ring-primary" 
            disabled={loading || !isPasswordValid || !doPasswordsMatch || !formData.first_name || !formData.last_name || !formData.email}
          >
            {loading ? (
              <>
                <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                Creating Account...
              </>
            ) : (
              'Create Account'
            )}
          </Button>

          <div className="text-center text-sm text-muted-foreground">
            Already have an account?{' '}
            <Button
              type="button"
              variant="link"
              size="sm"
              onClick={onSwitchToSignIn}
              disabled={loading}
              className="px-0 text-primary hover:text-primary/80"
            >
              Sign in
            </Button>
          </div>
        </CardFooter>
      </form>
    </Card>
  )
}