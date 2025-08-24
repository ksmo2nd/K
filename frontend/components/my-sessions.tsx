"use client"

import React, { useState, useEffect } from 'react'
import { Button } from '@/components/ui/button'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { Badge } from '@/components/ui/badge'
import { Progress } from '@/components/ui/progress'
import { api } from '@/lib/api'
import { toast } from 'sonner'
import { 
  Play, 
  Download, 
  Wifi, 
  WifiOff,
  Clock,
  CheckCircle,
  AlertCircle,
  RefreshCw,
  QrCode,
  Smartphone,
  Timer,
  Activity,
  Zap
} from 'lucide-react'

interface UserSession {
  id: string
  name: string
  size: string
  status: string
  progress_percent: number
  download_started_at: string
  expires_at?: string
  is_active: boolean
  can_activate: boolean
  data_remaining_mb: number
}

interface MySessionsProps {
  refreshTrigger?: number
}

export function MySessions({ refreshTrigger = 0 }: MySessionsProps) {
  const [sessions, setSessions] = useState<UserSession[]>([])
  const [loading, setLoading] = useState(true)
  const [activating, setActivating] = useState<string | null>(null)

  useEffect(() => {
    loadSessions()
  }, [refreshTrigger])

  const loadSessions = async () => {
    try {
      setLoading(true)
      const sessionsData = await api.getMySessions()
      setSessions(sessionsData)
    } catch (error) {
      console.error('Failed to load sessions:', error)
      toast.error('Failed to load your sessions')
    } finally {
      setLoading(false)
    }
  }

  const handleActivate = async (sessionId: string) => {
    if (activating) return

    try {
      setActivating(sessionId)
      const response = await api.activateSession(sessionId)
      
      if (response.success) {
        toast.success('Session activated successfully!', {
          description: 'Your internet session is now active'
        })
        await loadSessions() // Refresh sessions
      } else {
        throw new Error(response.message || 'Activation failed')
      }
    } catch (error: any) {
      console.error('Activation failed:', error)
      toast.error(error.message || 'Failed to activate session')
    } finally {
      setActivating(null)
    }
  }

  const getStatusIcon = (status: string) => {
    switch (status) {
      case 'downloading':
        return <Download className="h-4 w-4 text-blue-500 animate-bounce" />
      case 'transferring':
        return <RefreshCw className="h-4 w-4 text-kswifi-cyan animate-spin" />
      case 'stored':
        return <CheckCircle className="h-4 w-4 text-green-500" />
      case 'active':
        return <Activity className="h-4 w-4 text-kswifi-cyan animate-pulse" />
      case 'exhausted':
        return <AlertCircle className="h-4 w-4 text-red-500" />
      case 'expired':
        return <Clock className="h-4 w-4 text-gray-500" />
      default:
        return <Clock className="h-4 w-4 text-gray-500" />
    }
  }

  const getStatusText = (status: string) => {
    switch (status) {
      case 'downloading':
        return 'Downloading'
      case 'transferring':
        return 'Transferring to eSIM'
      case 'stored':
        return 'Ready to activate'
      case 'active':
        return 'Active'
      case 'exhausted':
        return 'Session finished'
      case 'expired':
        return 'Expired'
      default:
        return status
    }
  }

  const getStatusBadgeVariant = (status: string) => {
    switch (status) {
      case 'active':
        return 'default'
      case 'stored':
        return 'secondary'
      case 'exhausted':
      case 'expired':
        return 'destructive'
      default:
        return 'outline'
    }
  }

  const formatDataSize = (mb: number) => {
    if (mb >= 999999) return 'Unlimited'
    if (mb >= 1024) return `${(mb / 1024).toFixed(1)}GB`
    return `${mb}MB`
  }

  const formatTimeAgo = (dateString: string) => {
    const date = new Date(dateString)
    const now = new Date()
    const diffInHours = Math.floor((now.getTime() - date.getTime()) / (1000 * 60 * 60))
    
    if (diffInHours < 1) return 'Just now'
    if (diffInHours < 24) return `${diffInHours}h ago`
    const diffInDays = Math.floor(diffInHours / 24)
    return `${diffInDays}d ago`
  }

  const formatExpiryTime = (dateString: string) => {
    const date = new Date(dateString)
    const now = new Date()
    const diffInHours = Math.floor((date.getTime() - now.getTime()) / (1000 * 60 * 60))
    
    if (diffInHours < 0) return 'Expired'
    if (diffInHours < 24) return `${diffInHours}h left`
    const diffInDays = Math.floor(diffInHours / 24)
    return `${diffInDays}d left`
  }

  if (loading) {
    return (
      <Card className="w-full max-w-4xl mx-auto bg-card border border-border">
        <CardHeader>
          <CardTitle className="flex items-center space-x-2">
            <Smartphone className="h-5 w-5 text-kswifi-cyan" />
            <span>My Internet Sessions</span>
          </CardTitle>
        </CardHeader>
        <CardContent>
          <div className="space-y-4">
            {[1, 2, 3].map((i) => (
              <div key={i} className="h-20 bg-muted animate-pulse rounded-lg"></div>
            ))}
          </div>
        </CardContent>
      </Card>
    )
  }

  if (sessions.length === 0) {
    return (
      <Card className="w-full max-w-4xl mx-auto bg-card border border-border">
        <CardHeader>
          <CardTitle className="flex items-center space-x-2">
            <Smartphone className="h-5 w-5 text-kswifi-cyan" />
            <span>My Internet Sessions</span>
          </CardTitle>
        </CardHeader>
        <CardContent>
          <div className="text-center py-8">
            <WifiOff className="h-12 w-12 text-muted-foreground mx-auto mb-4" />
            <h3 className="text-lg font-medium text-foreground mb-2">No sessions yet</h3>
            <p className="text-muted-foreground">
              Download your first internet session to get started
            </p>
          </div>
        </CardContent>
      </Card>
    )
  }

  return (
    <Card className="w-full max-w-4xl mx-auto bg-card border border-border">
      <CardHeader>
        <div className="flex items-center justify-between">
          <CardTitle className="flex items-center space-x-2">
            <Smartphone className="h-5 w-5 text-kswifi-cyan" />
            <span>My Internet Sessions</span>
          </CardTitle>
          <Button 
            variant="outline" 
            size="sm" 
            onClick={loadSessions}
            disabled={loading}
          >
            <RefreshCw className={`h-4 w-4 mr-2 ${loading ? 'animate-spin' : ''}`} />
            Refresh
          </Button>
        </div>
      </CardHeader>

      <CardContent>
        <div className="space-y-4">
          {sessions.map((session) => (
            <Card key={session.id} className="border border-border bg-muted/30">
              <CardContent className="p-4">
                <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
                  <div className="flex items-start space-x-4 flex-1">
                    {/* Status Icon */}
                    <div className="flex-shrink-0 mt-1">
                      {getStatusIcon(session.status)}
                    </div>

                    {/* Session Details */}
                    <div className="flex-1 min-w-0">
                      <div className="flex items-center space-x-2 mb-2">
                        <h3 className="font-semibold text-foreground">
                          {session.name}
                        </h3>
                        <Badge variant={getStatusBadgeVariant(session.status)}>
                          {getStatusText(session.status)}
                        </Badge>
                        {session.size.includes('Unlimited') && (
                          <Badge variant="secondary" className="bg-kswifi-cyan/20 text-kswifi-cyan">
                            <Zap className="h-3 w-3 mr-1" />
                            UNLIMITED
                          </Badge>
                        )}
                      </div>

                      {/* Progress Bar for Downloading */}
                      {(session.status === 'downloading' || session.status === 'transferring') && (
                        <div className="mb-3">
                          <Progress value={session.progress_percent} className="h-2 mb-1" />
                          <div className="flex justify-between text-xs text-muted-foreground">
                            <span>
                              {session.status === 'downloading' ? 'Downloading session...' : 'Transferring to eSIM...'}
                            </span>
                            <span>{session.progress_percent}%</span>
                          </div>
                        </div>
                      )}

                      {/* Session Stats */}
                      <div className="flex items-center space-x-4 text-sm text-muted-foreground">
                        <div className="flex items-center space-x-1">
                          <Download className="h-3 w-3" />
                          <span>Downloaded {formatTimeAgo(session.download_started_at)}</span>
                        </div>
                        
                        {session.is_active && (
                          <div className="flex items-center space-x-1">
                            <Activity className="h-3 w-3 text-kswifi-cyan" />
                            <span>
                              {formatDataSize(session.data_remaining_mb)} remaining
                            </span>
                          </div>
                        )}
                        
                        {session.expires_at && (
                          <div className="flex items-center space-x-1">
                            <Timer className="h-3 w-3" />
                            <span>{formatExpiryTime(session.expires_at)}</span>
                          </div>
                        )}
                      </div>
                    </div>

                  </div>

                  {/* Action Buttons - Mobile optimized */}
                  <div className="flex flex-row sm:flex-col gap-2 sm:space-y-2 justify-start sm:justify-end w-full sm:w-auto">
                      {session.can_activate && (
                        <Button 
                          onClick={() => handleActivate(session.id)}
                          disabled={activating === session.id}
                          className="bg-kswifi-cyan hover:bg-kswifi-cyan-dark text-black font-medium min-w-[100px] flex-1 sm:flex-none"
                          size="sm"
                        >
                          {activating === session.id ? (
                            <div className="flex items-center space-x-2">
                              <RefreshCw className="h-4 w-4 animate-spin" />
                              <span>Activating</span>
                            </div>
                          ) : (
                            <div className="flex items-center space-x-2">
                              <Play className="h-4 w-4" />
                              <span>Activate</span>
                            </div>
                          )}
                        </Button>
                      )}

                    {session.is_active && (
                      <Button 
                        variant="outline" 
                        size="sm"
                        className="border-kswifi-cyan text-kswifi-cyan hover:bg-kswifi-cyan/10 flex-1 sm:flex-none"
                      >
                        <QrCode className="h-4 w-4 mr-2" />
                        QR Code
                      </Button>
                    )}

                    {(session.status === 'exhausted' || session.status === 'expired') && (
                      <Button 
                        variant="outline" 
                        size="sm"
                        disabled
                        className="opacity-50 flex-1 sm:flex-none"
                      >
                        <AlertCircle className="h-4 w-4 mr-2" />
                        {session.status === 'exhausted' ? 'Finished' : 'Expired'}
                      </Button>
                    )}
                  </div>
                </div>
              </CardContent>
            </Card>
          ))}
        </div>

        {/* How to Activate Info */}
        {sessions.some(s => s.can_activate) && (
          <div className="mt-6 p-4 bg-kswifi-cyan/10 border border-kswifi-cyan/20 rounded-lg">
            <div className="flex items-start space-x-3">
              <QrCode className="h-5 w-5 text-kswifi-cyan flex-shrink-0 mt-0.5" />
              <div className="text-sm text-foreground">
                <p className="font-medium mb-1">Ready to go offline?</p>
                <p className="text-muted-foreground">
                  Click "Activate" to enable your downloaded session. You'll get a QR code to add the eSIM to your phone, 
                  then you can use the internet even without WiFi!
                </p>
              </div>
            </div>
          </div>
        )}
      </CardContent>
    </Card>
  )
}