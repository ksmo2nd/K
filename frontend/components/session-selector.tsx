"use client"

import React, { useState, useEffect } from 'react'
import { Button } from '@/components/ui/button'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { Badge } from '@/components/ui/badge'
import { Progress } from '@/components/ui/progress'
import { api } from '@/lib/api'
import { toast } from 'sonner'
import { useWiFiStatus } from '@/hooks/use-wifi-status'
import { 
  Download, 
  Wifi, 
  Smartphone, 
  CheckCircle, 
  Clock,
  Zap,
  Shield,
  Star,
  ArrowRight,
  Gift
} from 'lucide-react'

interface SessionOption {
  id: string
  name: string
  size: string
  data_mb: number
  price_ngn: number
  price_usd: number
  validity_days: number | null
  plan_type: string
  is_unlimited: boolean
  is_free: boolean
  description: string
  features: string[]
  source_network?: string
  network_quality?: string
}

interface SessionSelectorProps {
  onSessionDownload: (sessionId: string) => void
}

export function SessionSelector({ onSessionDownload }: SessionSelectorProps) {
  const [sessions, setSessions] = useState<SessionOption[]>([])
  const [selectedSession, setSelectedSession] = useState<string | null>(null)
  const [isDownloading, setIsDownloading] = useState(false)
  const [downloadProgress, setDownloadProgress] = useState(0)
  const [currentDownloadId, setCurrentDownloadId] = useState<string | null>(null)
  const [freeQuota, setFreeQuota] = useState<any>(null)
  const [loading, setLoading] = useState(true)
  
  // Get WiFi connection status
  const wifiStatus = useWiFiStatus()

  useEffect(() => {
    loadSessions()
    loadFreeQuota()
  }, [wifiStatus.networkName]) // Reload when WiFi network changes

  const loadSessions = async () => {
    try {
      console.log('🌐 WiFi Status:', wifiStatus)
      console.log('🌐 Loading sessions...')
      
      // Always load sessions - backend handles WiFi detection gracefully
      // Pass WiFi network name if available for personalization
      const networkName = wifiStatus.isConnected && wifiStatus.networkName ? wifiStatus.networkName : undefined
      if (networkName) {
        console.log('🌐 Loading sessions from WiFi network:', networkName)
      } else {
        console.log('🌐 Loading default sessions (no specific WiFi network)')
      }
      
      const sessionsData = await api.getAvailableSessions(networkName)
      setSessions(sessionsData)
      
      if (sessionsData.length === 0) {
        toast.info('No sessions available at the moment')
      } else {
        console.log(`✅ Loaded ${sessionsData.length} sessions`)
      }
    } catch (error) {
      console.error('Failed to load sessions:', error)
      toast.error('Failed to load available sessions')
    } finally {
      setLoading(false)
    }
  }

  const loadFreeQuota = async () => {
    try {
      const quotaData = await api.getFreeQuotaUsage()
      setFreeQuota(quotaData.data)
    } catch (error) {
      console.error('Failed to load quota:', error)
    }
  }

  const handleDownload = async (sessionId: string) => {
    if (isDownloading) return

    try {
      setIsDownloading(true)
      setCurrentDownloadId(sessionId)
      setDownloadProgress(0)

      // Start session download
      const response = await api.startSessionDownload(sessionId)
      
      if (response.success) {
        toast.success('Session download started!')
        onSessionDownload(sessionId)
        
        // Start progress simulation
        simulateDownloadProgress(response.data.session_id)
      } else {
        throw new Error(response.message || 'Download failed')
      }
    } catch (error: any) {
      console.error('Download failed:', error)
      toast.error(error.message || 'Failed to start session download')
      setIsDownloading(false)
      setCurrentDownloadId(null)
    }
  }

  const simulateDownloadProgress = (sessionId: string) => {
    let progress = 0
    const interval = setInterval(async () => {
      progress += Math.random() * 15 + 5 // Increment by 5-20%
      
      if (progress >= 100) {
        progress = 100
        clearInterval(interval)
        setIsDownloading(false)
        setCurrentDownloadId(null)
        setDownloadProgress(0)
        
        // Check actual status
        try {
          const status = await api.getSessionStatus(sessionId)
          if (status.data.status === 'stored') {
            toast.success('Internet session downloaded successfully!', {
              description: 'You can now activate it for offline use'
            })
          }
        } catch (error) {
          console.error('Failed to check status:', error)
        }
      } else {
        setDownloadProgress(progress)
      }
    }, 800) // Update every 800ms for smooth animation
  }

  const getSessionIcon = (session: SessionOption) => {
    if (session.is_free) return <Gift className="h-5 w-5 text-green-500" />
    if (session.is_unlimited) return <Zap className="h-5 w-5 text-kswifi-cyan" />
    return <Download className="h-5 w-5 text-blue-500" />
  }

  const formatPrice = (session: SessionOption) => {
    if (session.is_free) return 'FREE'
    return `₦${session.price_ngn.toLocaleString()}`
  }

  const getValidityText = (days: number) => {
    if (days === 7) return '1 week'
    if (days === 30) return '1 month'
    return `${days} days`
  }

  if (loading) {
    return (
      <Card className="w-full max-w-4xl mx-auto bg-card border border-border">
        <CardHeader className="text-center">
          <div className="flex items-center justify-center space-x-2 mb-2">
            <Wifi className="h-6 w-6 text-kswifi-cyan animate-pulse" />
            <CardTitle className="text-xl font-semibold text-foreground">Loading Sessions...</CardTitle>
          </div>
        </CardHeader>
        <CardContent>
          <div className="space-y-4">
            {[1, 2, 3].map((i) => (
              <div key={i} className="h-24 bg-muted animate-pulse rounded-lg"></div>
            ))}
          </div>
        </CardContent>
      </Card>
    )
  }

  return (
    <Card className="w-full max-w-4xl mx-auto bg-card border border-border">
      <CardHeader className="text-center">
        <div className="flex items-center justify-center space-x-2 mb-2">
          <Wifi className="h-6 w-6 text-kswifi-cyan" />
          <CardTitle className="text-xl font-semibold text-foreground">Download Internet Sessions</CardTitle>
        </div>
        <p className="text-sm text-muted-foreground">
          Download internet sessions on WiFi to use later offline via eSIM
        </p>
        
        {/* Free Quota Display */}
        {freeQuota && (
          <div className="mt-4 p-3 bg-muted rounded-lg">
            <div className="flex items-center justify-between text-sm">
              <span className="text-muted-foreground">Free Quota This Month</span>
              <span className="font-medium text-foreground">
                {(freeQuota.used_mb / 1024).toFixed(1)}GB / {(freeQuota.limit_mb / 1024).toFixed(0)}GB
              </span>
            </div>
            <Progress 
              value={freeQuota.percentage_used} 
              className="mt-2 h-2"
            />
          </div>
        )}
      </CardHeader>

      <CardContent>
        {/* Download Progress */}
        {isDownloading && (
          <div className="mb-6 p-4 bg-kswifi-cyan/10 border border-kswifi-cyan/20 rounded-lg">
            <div className="flex items-center space-x-3 mb-3">
              <Download className="h-5 w-5 text-kswifi-cyan animate-bounce" />
              <span className="font-medium text-foreground">Downloading Internet Session...</span>
            </div>
            <Progress value={downloadProgress} className="h-3 mb-2" />
            <div className="flex justify-between text-xs text-muted-foreground">
              <span>Transferring to eSIM storage</span>
              <span>{Math.round(downloadProgress)}% complete</span>
            </div>
          </div>
        )}

        <div className="space-y-4">
          {sessions.map((session) => (
            <Card 
              key={session.id} 
              className={`transition-all duration-200 hover:shadow-md border ${
                session.is_free 
                  ? 'border-green-500/30 bg-green-500/5' 
                  : session.is_unlimited 
                  ? 'border-kswifi-cyan/30 bg-kswifi-cyan/5'
                  : 'border-border bg-card'
              }`}
            >
              <CardContent className="p-4">
                <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
                  <div className="flex items-start space-x-4 flex-1">
                    {/* Session Icon */}
                    <div className="flex-shrink-0 mt-1">
                      {getSessionIcon(session)}
                    </div>

                    {/* Session Details */}
                    <div className="flex-1 min-w-0">
                      <div className="flex items-center space-x-2 mb-1">
                        <h3 className="font-semibold text-foreground text-lg">
                          {session.size}
                        </h3>
                        {session.is_free && (
                          <Badge variant="secondary" className="bg-green-500/20 text-green-700 dark:text-green-300">
                            FREE
                          </Badge>
                        )}
                        {session.is_unlimited && (
                          <Badge variant="secondary" className="bg-kswifi-cyan/20 text-kswifi-cyan">
                            <Star className="h-3 w-3 mr-1" />
                            UNLIMITED
                          </Badge>
                        )}
                      </div>
                      
                      <p className="text-sm text-muted-foreground mb-3">
                        {session.description}
                      </p>

                      {/* Features */}
                      <div className="flex flex-wrap gap-2 mb-3">
                        {session.features.slice(0, 3).map((feature, index) => (
                          <div key={index} className="flex items-center space-x-1 text-xs text-muted-foreground">
                            <CheckCircle className="h-3 w-3 text-kswifi-cyan" />
                            <span>{feature}</span>
                          </div>
                        ))}
                      </div>

                      {/* Session Info */}
                      <div className="flex items-center space-x-4 text-xs text-muted-foreground">
                        <div className="flex items-center space-x-1">
                          <Clock className="h-3 w-3" />
                          <span>Valid {getValidityText(session.validity_days || 0)}</span>
                        </div>
                        <div className="flex items-center space-x-1">
                          <Smartphone className="h-3 w-3" />
                          <span>Activate via eSIM</span>
                        </div>
                        <div className="flex items-center space-x-1">
                          <Shield className="h-3 w-3" />
                          <span>Offline capable</span>
                        </div>
                      </div>
                    </div>

                  </div>

                  {/* Price & Download - Mobile optimized */}
                  <div className="flex sm:flex-col items-center sm:items-end justify-between sm:justify-start sm:space-y-3 w-full sm:w-auto">
                    <div className="text-left sm:text-right">
                      <div className="text-xl sm:text-2xl font-bold text-foreground">
                        {formatPrice(session)}
                      </div>
                      {!session.is_free && (
                        <div className="text-xs text-muted-foreground">
                          per {getValidityText(session.validity_days || 0)}
                        </div>
                      )}
                    </div>

                    <Button 
                      onClick={() => handleDownload(session.id)}
                      disabled={isDownloading || (currentDownloadId === session.id)}
                      className={`${
                        session.is_free 
                          ? 'bg-primary hover:bg-primary/90 text-primary-foreground'
                          : session.is_unlimited
                          ? 'bg-primary hover:bg-primary/90 text-primary-foreground'
                          : 'bg-primary hover:bg-primary/90 text-primary-foreground'
                      } transition-all duration-200 font-medium min-w-[120px] sm:min-w-[140px]`}
                      size="sm"
                    >
                      {currentDownloadId === session.id ? (
                        <div className="flex items-center space-x-2">
                          <Download className="h-4 w-4 animate-spin" />
                          <span>Downloading</span>
                        </div>
                      ) : (
                        <div className="flex items-center space-x-2">
                          <Download className="h-4 w-4" />
                          <span>Download</span>
                          <ArrowRight className="h-3 w-3" />
                        </div>
                      )}
                    </Button>
                  </div>
                </div>
              </CardContent>
            </Card>
          ))}
        </div>

        {/* Info Footer */}
        <div className="mt-6 p-4 bg-muted rounded-lg">
          <div className="flex items-start space-x-3">
            <div className="flex-shrink-0 mt-0.5">
              <div className="w-2 h-2 bg-kswifi-cyan rounded-full"></div>
            </div>
            <div className="text-sm text-muted-foreground">
              <p className="font-medium text-foreground mb-1">How it works:</p>
              <p>
                1. Connect to WiFi and download an internet session
                <br />
                2. Session is stored on your phone's eSIM chip
                <br />
                3. When offline, activate the eSIM to use your downloaded session
                <br />
                4. Browse normally until the session is finished
              </p>
            </div>
          </div>
        </div>
      </CardContent>
    </Card>
  )
}