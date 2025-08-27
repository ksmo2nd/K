"use client"

import { useState, useEffect } from "react"
import { Button } from "@/components/ui/button"
import { Card } from "@/components/ui/card"
import { DataMeter } from "@/components/data-meter"
import { WifiStatus } from "@/components/wifi-status"
import { ActionButton } from "@/components/action-button"
import { HistoryItem } from "@/components/history-item"
import { NotificationPopup } from "@/components/notification-popup"
import { DataPackSelector } from "@/components/data-pack-selector"
import { SessionSelector } from "@/components/session-selector"
import { MySessions } from "@/components/my-sessions"
import { SignInForm, SignUpForm, PasswordResetForm } from "@/components/auth"
import { ProtectedRoute } from "@/components/auth/protected-route"
import { useAuth } from "@/lib/auth-context"
import { useUserProfile } from "@/hooks/use-user-profile"
import { useWiFiStatus } from "@/hooks/use-wifi-status"
import { SecurityProvider, useAppSecurity } from "@/lib/security-context"
import { SecurityIndicator } from "@/components/security-indicator"
import { HelpCenter } from "@/components/help-center"
import { AboutApp } from "@/components/about-app"
import { ESIMQRPopup } from "@/components/esim-qr-popup"
import { DualESIMPopup } from "@/components/dual-esim-popup"
import { apiService } from "@/lib/api"
import { toast } from "sonner"
import {
  Download,
  Power,
  Play,
  Settings,
  User,
  LogOut,
  Smartphone,
  QrCode,
  History,
  HelpCircle,
  Shield,
  Info,
} from "lucide-react"

type AuthScreen = "signin" | "signup" | "reset-password"
type AppScreen = "onboarding" | "dashboard" | "settings" | "help" | "about"

export default function KSWiFiApp() {
  // Auth state
  const { user, loading: authLoading, signOut } = useAuth()
  const { profile, loading: profileLoading } = useUserProfile()
  
  // Real WiFi status
  const wifiStatus = useWiFiStatus()
  
  // App state
  const [currentScreen, setCurrentScreen] = useState<AppScreen>("onboarding")
  const [authScreen, setAuthScreen] = useState<AuthScreen>("signin")
  const [showDataPackSelector, setShowDataPackSelector] = useState(false)
  const [notification, setNotification] = useState<{
    type: "success" | "warning" | "info"
    title: string
    message: string
    isVisible: boolean
  }>({ type: "info", title: "", message: "", isVisible: false })
  const [securityEnabled, setSecurityEnabled] = useState(true)

  // Data state
  const [dataPacks, setDataPacks] = useState<any[]>([])
  const [esims, setEsims] = useState<any[]>([])
  const [dataPackStats, setDataPackStats] = useState<any>(null)
  
  // Session state
  const [showSessionSelector, setShowSessionSelector] = useState(false)
  const [sessionsRefreshTrigger, setSessionsRefreshTrigger] = useState(0)
  
  // eSIM QR popup state
  const [showESIMPopup, setShowESIMPopup] = useState(false)
  const [esimData, setESIMData] = useState<any>(null)
  
  // Dual eSIM popup state
  const [showDualESIMPopup, setShowDualESIMPopup] = useState(false)
  const [dualESIMData, setDualESIMData] = useState<any>(null)
  const [privatePassword, setPrivatePassword] = useState<string>("")

  // Check for URL messages (like password reset success)
  useEffect(() => {
    const urlParams = new URLSearchParams(window.location.search)
    const message = urlParams.get('message')
    const error = urlParams.get('error')

    if (message === 'password_updated') {
      toast.success('Password updated successfully!')
      // Clean URL
      window.history.replaceState({}, '', window.location.pathname)
    } else if (error) {
      switch (error) {
        case 'invalid_reset_link':
          toast.error('Invalid or expired reset link')
          break
        case 'reset_error':
          toast.error('An error occurred during password reset')
          break
        default:
          toast.error('An error occurred')
      }
      // Clean URL
      window.history.replaceState({}, '', window.location.pathname)
    }
  }, [])

  // Set initial screen based on auth state
  useEffect(() => {
    if (!authLoading) {
      if (user) {
        setCurrentScreen("dashboard")
        loadUserData()
      } else {
        setCurrentScreen("onboarding")
      }
    }
  }, [user, authLoading])

  const loadUserData = async () => {
    if (!user) return

    try {
      // Load data packs
      const userDataPacks = await apiService.getDataPacks()
      setDataPacks(userDataPacks)

      // Load eSIMs
      const userEsims = await apiService.getESIMs()
      setEsims(userEsims)

      // Load stats
      const stats = await apiService.getDataPackStats()
      setDataPackStats(stats)
    } catch (error) {
      console.error('Error loading user data:', error)
      toast.error('Failed to load user data')
    }
  }

  // Real user data (no mocks)
  const userData = profile ? {
    name: `${profile.first_name} ${profile.last_name}`,
    email: profile.email,
    currentData: dataPackStats?.used_data_mb || 0,
    totalData: dataPackStats?.total_data_mb || 0,
  } : user ? {
    name: user.user_metadata?.first_name && user.user_metadata?.last_name 
      ? `${user.user_metadata.first_name} ${user.user_metadata.last_name}`
      : user.email?.split('@')[0] || 'User',
    email: user.email || "",
    currentData: 0,
    totalData: 0,
  } : {
    name: "Sign in to continue",
    email: "",
    currentData: 0,
    totalData: 0,
  }

  // Recent history from actual data only
  const recentHistory = dataPacks.length > 0 ? dataPacks.map(pack => ({
    size: pack.name,
    date: new Date(pack.created_at).toLocaleDateString(),
    used: `${pack.used_data_mb}MB`,
    status: pack.status as "completed" | "active" | "expired"
  })) : []

  const showNotification = (type: "success" | "warning" | "info", title: string, message: string) => {
    setNotification({ type, title, message, isVisible: true })
  }

  const handleSignOut = async () => {
    try {
      await signOut()
      setCurrentScreen("onboarding")
      setDataPacks([])
      setEsims([])
      setDataPackStats(null)
      toast.success("Signed out successfully")
    } catch (error) {
      console.error('Logout error:', error)
      toast.error("Error signing out")
    }
  }

  const handleSessionDownload = () => {
    if (!wifiStatus.isConnected || !wifiStatus.isOnline) {
      showNotification("warning", "Internet Required", "Connect to the internet to download sessions")
      return
    }
    if (!user) {
      showNotification("warning", "Sign In Required", "Please sign in to download sessions")
      return
    }
    setShowSessionSelector(true)
  }

  const handleSessionDownloadComplete = (sessionId: string) => {
    setShowSessionSelector(false)
    setSessionsRefreshTrigger(prev => prev + 1)
    toast.success("Session download started!", {
      description: "Your internet session is being prepared"
    })
  }

  const handleESIMSetup = async () => {
    if (!user) {
      showNotification("warning", "Sign In Required", "Please sign in to setup eSIM")
      return
    }

    try {
      // Get user's active sessions
      const sessions = await apiService.getMySessions()
      console.log('🔍 DUAL eSIM DEBUG: Total sessions:', sessions.length)
      
      const activeSessions = sessions.filter(session => session.status === 'active')
      console.log('🔍 DUAL eSIM DEBUG: Active sessions:', activeSessions.length)

      if (activeSessions.length === 0) {
        showNotification("info", "No Active Sessions", "Please activate a data pack first, then generate eSIM options")
        return
      }

      // Use the first active session
      const session = activeSessions[0]
      console.log('🔍 DUAL eSIM DEBUG: Using session:', { id: session.id, data_mb: session.data_mb })
      
      // Show password prompt for private access
      const password = await showPasswordPrompt()
      
      // Generate dual eSIM options
      console.log('🔍 DUAL eSIM DEBUG: Generating options with password:', !!password)
      const result = await apiService.generateDualESIMOptions(
        session.id, 
        session.data_mb, 
        password || undefined
      )
      
      console.log('✅ DUAL eSIM DEBUG: Options generated:', result)
      
      // Show dual eSIM popup
      setDualESIMData(result)
      setShowDualESIMPopup(true)
      
    } catch (error: any) {
      console.error('❌ DUAL eSIM ERROR:', error)
      showNotification("warning", "eSIM Setup Failed", error.message || "Failed to generate eSIM options")
    }
  }

  const showPasswordPrompt = (): Promise<string | null> => {
    return new Promise((resolve) => {
      const password = prompt(
        "🔒 Private eSIM Access (Optional)\n\nEnter password for private eSIM profiles:\n(Leave empty for public WiFi only)"
      )
      resolve(password?.trim() || null)
    })
  }

  const handleGenerateESIM = async (sessionId?: string, dataSizeMB?: number) => {
    try {
      console.log('🔄 Generating eSIM QR code...', { sessionId, dataSizeMB })
      
      // Show loading toast
      const loadingToast = toast.loading('Generating eSIM QR code...', {
        description: 'Please wait while we prepare your eSIM'
      })
      
      // Generate eSIM QR code
      const result = await apiService.generateESIM(sessionId, dataSizeMB)
      
      console.log('✅ eSIM generated successfully:', result)
      console.log('🔍 ESIM DEBUG: result.success =', result.success)
      console.log('🔍 ESIM DEBUG: result keys =', Object.keys(result))
      
      // Dismiss loading toast
      toast.dismiss(loadingToast)
      
      if (result.success) {
        console.log('🔍 ESIM DEBUG: Setting eSIM data and showing popup')
        // Store eSIM data and show popup
        setESIMData(result)
        setShowESIMPopup(true)
        console.log('🔍 ESIM DEBUG: showESIMPopup set to true')
        
        toast.success('eSIM QR Code Generated!', {
          description: 'Scan the QR code to activate your eSIM'
        })
      } else {
        throw new Error('eSIM generation failed')
      }
      
    } catch (error: any) {
      console.error('❌ eSIM generation error:', error)
      
      toast.error('Failed to generate eSIM', {
        description: error?.message || 'Please try again later'
      })
    }
  }

  const closeESIMPopup = () => {
    setShowESIMPopup(false)
    setESIMData(null)
  }

  const closeDualESIMPopup = () => {
    setShowDualESIMPopup(false)
    setDualESIMData(null)
    setPrivatePassword("")
  }

  const handleDataPackActivation = async () => {
    if (!user) {
      showNotification("warning", "Sign In Required", "Please sign in to activate data packs")
      return
    }

    try {
      // Get user's downloaded sessions
      const sessions = await apiService.getMySessions()
      console.log('🔍 FRONTEND: All sessions:', sessions)
      
      const availableSessions = sessions.filter(session => session.can_activate)
      const activeSessions = sessions.filter(session => session.status === 'active')
      
      console.log('🔍 FRONTEND: Available sessions:', availableSessions)
      console.log('🔍 FRONTEND: Active sessions:', activeSessions)

      // Check if user already has active sessions
      if (activeSessions.length > 0) {
        const activeSession = activeSessions[0]
        showNotification("info", "Session Already Active", `You have an active ${activeSession.data_mb}MB session. Generate eSIM to use it for internet access.`)
        return
      }

      if (availableSessions.length === 0) {
        showNotification("info", "No Data Packs Available", "Download a session first, then activate it here")
        return
      }

      // If only one session available, activate it directly
      if (availableSessions.length === 1) {
        const session = availableSessions[0]
        await apiService.activateSession(session.id)
        setSessionsRefreshTrigger(prev => prev + 1)
        showNotification("success", "Data Pack Activated!", `${session.data_mb}MB session is now active`)
      } else {
        // If multiple sessions, show a selection
        showNotification("info", "Multiple Sessions Available", "Check 'My Sessions' below to choose which one to activate")
      }
    } catch (error: any) {
      console.error('Error activating data pack:', error)
      showNotification("warning", "Activation Failed", error.message || "Failed to activate data pack")
    }
  }

  const handleDataPackSelect = async (pack: { size: string; price: string }) => {
    setShowDataPackSelector(false)
    
    if (!user) {
      showNotification("warning", "Authentication Required", "Please sign in first")
      return
    }

    try {
      // Create data pack through API
      const result = await apiService.createDataPack({
        bundle_name: pack.size,
        validity_days: 30
      })

      showNotification("success", "Data Credits Purchased!", `${pack.size} credits added to your account`)
      
      // Reload user data
      await loadUserData()
    } catch (error: any) {
      console.error('Error purchasing data pack:', error)
      showNotification("warning", "Purchase Failed", error.message || "Failed to purchase data credits")
    }
  }

  // Handle authentication success
  const handleAuthSuccess = () => {
    setCurrentScreen("dashboard")
    toast.success(`Welcome ${profile?.first_name || 'back'}!`)
  }

  // Onboarding Screen
  const renderOnboarding = () => (
    <div className="min-h-screen bg-background flex items-center justify-center p-4">
      <Card className="w-full max-w-md text-center p-8 bg-card border-border">
        <div className="mb-8">
          <div className="w-20 h-20 bg-primary rounded-full flex items-center justify-center mx-auto mb-4 animate-pulse-cyan">
            <Smartphone className="w-10 h-10 text-primary-foreground" />
          </div>
          <h1 className="text-3xl font-bold text-foreground mb-2">KSWiFi</h1>
          <p className="text-muted-foreground mb-6">Virtual eSIM Data Manager</p>
          <p className="text-sm text-muted-foreground">
            Download internet sessions on WiFi, use offline via eSIM
          </p>
        </div>
        
        <div className="space-y-3">
          <Button 
            className="w-full bg-primary text-primary-foreground hover:bg-primary/90" 
            size="lg"
            onClick={() => {
              console.log("🔥 GET STARTED BUTTON CLICKED")
              setAuthScreen("signup")
              setCurrentScreen("dashboard") // This will trigger auth screen via logic
            }}
          >
            Get Started
          </Button>
          <Button 
            variant="outline" 
            className="w-full border-border text-foreground hover:bg-muted" 
            size="lg"
            onClick={() => {
              console.log("🔥 SIGN IN BUTTON CLICKED")
              setAuthScreen("signin")
              setCurrentScreen("dashboard") // This will trigger auth screen via logic
            }}
          >
            Sign In
          </Button>
        </div>
      </Card>
    </div>
  )

  // Authentication Screen
  const renderAuth = () => (
    <div className="min-h-screen bg-background flex items-center justify-center p-4">
      {/* Back to onboarding button */}
      <div className="absolute top-4 left-4">
        <Button
          variant="ghost"
          size="sm"
          onClick={() => {
            setAuthScreen("signin") // Reset to default
            setCurrentScreen("onboarding") // Go back to onboarding
          }}
          className="text-muted-foreground hover:text-foreground"
        >
          ← Back
        </Button>
      </div>

      {authScreen === "signin" && (
        <SignInForm
          onSuccess={handleAuthSuccess}
          onSwitchToSignUp={() => setAuthScreen("signup")}
          onForgotPassword={() => setAuthScreen("reset-password")}
        />
      )}
      {authScreen === "signup" && (
        <SignUpForm
          onSuccess={handleAuthSuccess}
          onSwitchToSignIn={() => setAuthScreen("signin")}
        />
      )}
      {authScreen === "reset-password" && (
        <PasswordResetForm
          onBack={() => setAuthScreen("signin")}
        />
      )}
    </div>
  )

  // Dashboard Screen (protected)
  const renderDashboard = () => (
    <div className="min-h-screen bg-background">
      <div className="max-w-md mx-auto bg-card shadow-2xl min-h-screen border-x border-border">
        {/* Header */}
        <div className="bg-gradient-to-r from-card to-muted text-foreground p-6 rounded-b-lg border-b border-border">
          <div className="flex justify-between items-center mb-4">
            <div>
              <h1 className="text-2xl font-bold">KSWiFi</h1>
              <p className="text-muted-foreground">Welcome, {userData.name.split(' ')[0]}</p>
            </div>
            <div className="flex space-x-2">
              <Button
                variant="ghost"
                size="sm"
                onClick={() => setCurrentScreen("settings")}
                className="text-muted-foreground hover:bg-muted/50 hover:text-foreground"
              >
                <Settings className="w-5 h-5" />
              </Button>
              <Button
                variant="ghost"
                size="sm"
                onClick={handleSignOut}
                className="text-muted-foreground hover:bg-muted/50 hover:text-foreground"
              >
                <LogOut className="w-5 h-5" />
              </Button>
            </div>
          </div>
          
          <WifiStatus />
          
          <SecurityIndicator />
        </div>

        {/* Data Usage */}
        <div className="p-6">
          <DataMeter 
            currentData={userData.currentData} 
            totalData={userData.totalData}
            unit="GB"
          />
        </div>

        {/* Action Buttons */}
        <div className="px-6 pb-6">
          <div className="grid grid-cols-2 gap-4">
            <ActionButton
              icon={Download}
              label="Download Session"
              description={wifiStatus.isConnected ? "Ready to Download" : "Internet Required"}
              onClick={handleSessionDownload}
            />
            <ActionButton
              icon={Play}
              label="Activate Data Pack"
              description="Use Downloaded"
              onClick={handleDataPackActivation}
            />
          </div>
          
          {/* Secondary Actions */}
          <div className="mt-4">
            <ActionButton
              icon={QrCode}
              label="Setup eSIM"
              description="Generate QR Code"
              onClick={handleESIMSetup}
              variant="secondary"
            />
          </div>
        </div>

        {/* Recent Activity */}
        <div className="px-6 pb-6">
          <div className="flex justify-between items-center mb-4">
            <h2 className="text-lg font-semibold text-foreground">Recent Activity</h2>
            <Button variant="ghost" size="sm" className="text-muted-foreground hover:text-foreground">
              <History className="w-4 h-4 mr-1" />
              View All
            </Button>
          </div>
          
          <div className="space-y-3">
            {recentHistory.slice(0, 3).map((item, index) => (
              <HistoryItem key={index} {...item} />
            ))}
          </div>
        </div>

        {/* My Sessions */}
        <div className="px-6 pb-6">
          <MySessions refreshTrigger={sessionsRefreshTrigger} />
        </div>
      </div>

      {/* Session Selector Modal */}
      {showSessionSelector && (
        <div className="fixed inset-0 bg-black/50 flex items-center justify-center p-4 z-50">
          <div className="bg-background rounded-lg max-w-4xl w-full max-h-[90vh] overflow-y-auto">
            <div className="p-4 border-b border-border flex justify-between items-center">
              <h2 className="text-lg font-semibold text-foreground">Download Internet Session</h2>
              <Button 
                variant="ghost" 
                size="sm" 
                onClick={() => setShowSessionSelector(false)}
                className="text-muted-foreground hover:text-foreground"
              >
                ✕
              </Button>
            </div>
            <div className="p-4">
              <SessionSelector onSessionDownload={handleSessionDownloadComplete} />
            </div>
          </div>
        </div>
      )}

      {/* Data Pack Selector Modal - Legacy */}
      {showDataPackSelector && (
        <DataPackSelector
          onSelect={handleDataPackSelect}
          onCancel={() => setShowDataPackSelector(false)}
        />
      )}

      {/* Notification */}
      {notification.isVisible && (
        <NotificationPopup
          type={notification.type}
          title={notification.title}
          message={notification.message}
          isVisible={notification.isVisible}
          onClose={() => setNotification(prev => ({ ...prev, isVisible: false }))}
        />
      )}

      {/* eSIM QR Code Popup */}
      <ESIMQRPopup
        isOpen={showESIMPopup}
        onClose={closeESIMPopup}
        esimData={esimData}
      />

      {/* Dual eSIM Options Popup */}
      <DualESIMPopup
        isOpen={showDualESIMPopup}
        onClose={closeDualESIMPopup}
        esimData={dualESIMData}
      />
    </div>
  )

  // Settings Screen
  const renderSettings = () => (
    <div className="min-h-screen bg-background">
      <div className="max-w-md mx-auto bg-card shadow-2xl min-h-screen border-x border-border">
        <div className="bg-gradient-to-r from-primary to-kswifi-cyan-dark text-primary-foreground p-6 rounded-b-3xl">
          <div className="flex items-center space-x-4">
            <Button
              variant="ghost"
              size="sm"
              onClick={() => setCurrentScreen("dashboard")}
              className="text-primary-foreground hover:bg-black/20"
            >
              ←
            </Button>
            <h1 className="text-2xl font-bold">Settings</h1>
          </div>
        </div>

        <div className="p-6 space-y-6">
          {/* Profile Section */}
          <div>
            <h2 className="text-lg font-semibold mb-4 text-foreground">Profile</h2>
            <div className="space-y-3">
              <div className="flex items-center justify-between p-3 bg-muted/20 border border-border rounded-lg">
                <div className="flex items-center space-x-3">
                  <User className="w-5 h-5 text-primary" />
                  <div>
                    <p className="font-medium text-foreground">{userData.name}</p>
                    <p className="text-sm text-muted-foreground">{userData.email}</p>
                  </div>
                </div>
              </div>
            </div>
          </div>

          {/* Security Section */}
          <div>
            <h2 className="text-lg font-semibold mb-4 text-foreground">Security</h2>
            <div className="space-y-3">
              <div className="flex items-center justify-between p-3 bg-muted/20 border border-border rounded-lg">
                <div className="flex items-center space-x-3">
                  <Shield className="w-5 h-5 text-primary" />
                  <span className="text-foreground">Enhanced Security</span>
                </div>
                <Button
                  variant="outline"
                  size="sm"
                  onClick={() => setSecurityEnabled(!securityEnabled)}
                  className="border-border text-foreground hover:bg-muted"
                >
                  {securityEnabled ? "Enabled" : "Enable"}
                </Button>
              </div>
            </div>
          </div>

          {/* Support Section */}
          <div>
            <h2 className="text-lg font-semibold mb-4 text-foreground">Support</h2>
            <div className="space-y-3">
              <Button 
                variant="ghost" 
                className="w-full justify-start p-3 text-foreground hover:bg-muted"
                onClick={() => setCurrentScreen("help")}
              >
                <HelpCircle className="w-5 h-5 mr-3 text-primary" />
                Help Center
              </Button>
              <Button 
                variant="ghost" 
                className="w-full justify-start p-3 text-foreground hover:bg-muted"
                onClick={() => setCurrentScreen("about")}
              >
                <Info className="w-5 h-5 mr-3 text-primary" />
                About KSWiFi
              </Button>
            </div>
          </div>

          {/* Sign Out */}
          <div className="pt-6 border-t border-border">
            <Button 
              variant="destructive" 
              className="w-full bg-destructive text-destructive-foreground hover:bg-destructive/90"
              onClick={handleSignOut}
            >
              <LogOut className="w-4 h-4 mr-2" />
              Sign Out
            </Button>
          </div>
        </div>
      </div>
    </div>
  )

  // Help Center Screen
  const renderHelpCenter = () => (
    <div className="min-h-screen bg-background">
      <div className="max-w-md mx-auto bg-card shadow-2xl min-h-screen border-x border-border">
        <div className="bg-gradient-to-r from-primary to-kswifi-cyan-dark text-primary-foreground p-6 rounded-b-3xl">
          <div className="flex items-center space-x-4">
            <Button
              variant="ghost"
              size="sm"
              onClick={() => setCurrentScreen("settings")}
              className="text-primary-foreground hover:bg-black/20"
            >
              ←
            </Button>
            <h1 className="text-2xl font-bold">Help Center</h1>
          </div>
        </div>
        <div className="p-4">
          <HelpCenter />
        </div>
      </div>
    </div>
  )

  // About App Screen
  const renderAboutApp = () => (
    <div className="min-h-screen bg-background">
      <div className="max-w-md mx-auto bg-card shadow-2xl min-h-screen border-x border-border">
        <div className="bg-gradient-to-r from-primary to-kswifi-cyan-dark text-primary-foreground p-6 rounded-b-3xl">
          <div className="flex items-center space-x-4">
            <Button
              variant="ghost"
              size="sm"
              onClick={() => setCurrentScreen("settings")}
              className="text-primary-foreground hover:bg-black/20"
            >
              ←
            </Button>
            <h1 className="text-2xl font-bold">About KSWiFi</h1>
          </div>
        </div>
        <div className="p-4">
          <AboutApp />
        </div>
      </div>
    </div>
  )

  // Loading state
  if (authLoading) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-background">
        <div className="text-center">
          <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-primary mx-auto mb-4"></div>
          <p className="text-muted-foreground">Loading...</p>
        </div>
      </div>
    )
  }

  // Render based on authentication state
  if (!user) {
    // Show auth screen if user clicked Get Started or Sign In, or if currentScreen is not onboarding
    if (currentScreen !== "onboarding" || authScreen === "signup" || authScreen === "reset-password") {
      return renderAuth()
    }
    // Otherwise show onboarding
    return renderOnboarding()
  }

  // Authenticated user screens
  return (
    <SecurityProvider>
      <ProtectedRoute fallback={renderAuth()}>
        {currentScreen === "dashboard" && renderDashboard()}
        {currentScreen === "settings" && renderSettings()}
        {currentScreen === "help" && renderHelpCenter()}
        {currentScreen === "about" && renderAboutApp()}
      </ProtectedRoute>
    </SecurityProvider>
  )
}