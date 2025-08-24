"use client"

import { useState } from 'react'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { Label } from '@/components/ui/label'
import { Card, CardHeader, CardTitle, CardContent, CardFooter } from '@/components/ui/card'
import { useAuth } from '@/lib/auth-context'
import { Eye, EyeOff, Loader2 } from 'lucide-react'

interface SignInFormProps {
  onSuccess?: () => void
  onSwitchToSignUp?: () => void
  onForgotPassword?: () => void
}

export function SignInForm({ onSuccess, onSwitchToSignUp, onForgotPassword }: SignInFormProps) {
  const { signIn } = useAuth()
  const [formData, setFormData] = useState({
    email: '',
    password: ''
  })
  const [showPassword, setShowPassword] = useState(false)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    setLoading(true)
    setError(null)

    try {
      const { data, error } = await signIn(formData.email, formData.password)
      
      if (error) {
        throw error
      }

      if (data?.user) {
        onSuccess?.()
      }
    } catch (err: any) {
      console.error('Sign in error:', err)
      setError(err.message || 'Failed to sign in. Please check your credentials.')
    } finally {
      setLoading(false)
    }
  }

  const handleInputChange = (field: string, value: string) => {
    setFormData(prev => ({ ...prev, [field]: value }))
    setError(null) // Clear error when user starts typing
  }

  return (
    <Card className="w-full max-w-md mx-auto bg-card border-border">
      <CardHeader className="text-center">
        <CardTitle className="text-2xl font-bold text-foreground">Welcome Back</CardTitle>
        <p className="text-muted-foreground">Sign in to your KSWiFi account</p>
      </CardHeader>
      
      <form onSubmit={handleSubmit}>
        <CardContent className="space-y-4">
          {error && (
            <div className="p-3 text-sm text-red-400 bg-red-900/20 border border-red-800 rounded-md">
              {error}
            </div>
          )}

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
            <Label htmlFor="password" className="text-foreground">Password</Label>
            <div className="relative">
              <Input
                id="password"
                type={showPassword ? 'text' : 'password'}
                placeholder="Enter your password"
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
          </div>

          <div className="flex justify-end">
            <Button
              type="button"
              variant="link"
              size="sm"
              onClick={onForgotPassword}
              disabled={loading}
              className="px-0 text-primary hover:text-primary/80"
            >
              Forgot password?
            </Button>
          </div>
        </CardContent>

        <CardFooter className="flex flex-col space-y-4">
          <Button 
            type="submit" 
            className="w-full bg-primary text-primary-foreground hover:bg-primary/90 focus:ring-primary" 
            disabled={loading || !formData.email || !formData.password}
          >
            {loading ? (
              <>
                <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                Signing In...
              </>
            ) : (
              'Sign In'
            )}
          </Button>

          <div className="text-center text-sm text-muted-foreground">
            Don't have an account?{' '}
            <Button
              type="button"
              variant="link"
              size="sm"
              onClick={onSwitchToSignUp}
              disabled={loading}
              className="px-0 text-primary hover:text-primary/80"
            >
              Sign up
            </Button>
          </div>
        </CardFooter>
      </form>
    </Card>
  )
}