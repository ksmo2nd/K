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
import { SignInForm, SignUpForm, PasswordResetForm } from "@/components/auth"
import { ProtectedRoute } from "@/components/auth/protected-route"
import { useAuth } from "@/lib/auth-context"
import { useUserProfile } from "@/hooks/use-user-profile"
import { apiService } from "@/lib/api"
import { toast } from "sonner"
import {
  Download,
  Power,
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
type AppScreen = "onboarding" | "dashboard" | "settings"

export default function KSWiFiApp() {
  // Auth state
  const { user, loading: authLoading, signOut } = useAuth()
  const { profile, loading: profileLoading } = useUserProfile()
  
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
  const [securityEnabled, setSecurityEnabled] = useState(false)

  // Data state
  const [dataPacks, setDataPacks] = useState<any[]>([])
  const [esims, setEsims] = useState<any[]>([])
  const [dataPackStats, setDataPackStats] = useState<any>(null)

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

  // Mock data for demo (fallback when no real data)
  const userData = profile ? {
    name: `${profile.first_name} ${profile.last_name}`,
    email: profile.email,
    currentData: dataPackStats?.used_data_mb || 0,
    totalData: dataPackStats?.total_data_mb || 0,
    isWifiConnected: true,
    networkName: "CoffeeShop_WiFi",
  } : {
    name: "Guest User",
    email: "",
    currentData: 0,
    totalData: 0,
    isWifiConnected: true,
    networkName: "CoffeeShop_WiFi",
  }

  // Recent history from actual data or mock
  const recentHistory = dataPacks.length > 0 ? dataPacks.map(pack => ({
    size: pack.name,
    date: new Date(pack.created_at).toLocaleDateString(),
    used: `${pack.used_data_mb}MB`,
    status: pack.status as "completed" | "active" | "expired"
  })) : [
    { size: "No data packs", date: "Sign in to view", used: "0 GB", status: "completed" as const },
  ]

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

  const handleDataPackDownload = () => {
    if (!userData.isWifiConnected) {
      showNotification("warning", "WiFi Required", "Connect to WiFi to download packs")
      return
    }
    if (!user) {
      showNotification("warning", "Sign In Required", "Please sign in to purchase data packs")
      return
    }
    setShowDataPackSelector(true)
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

      showNotification("success", "Data Pack Purchased!", `${pack.size} pack added to your account`)
      
      // Reload user data
      await loadUserData()
    } catch (error: any) {
      console.error('Error purchasing data pack:', error)
      showNotification("warning", "Purchase Failed", error.message || "Failed to purchase data pack")
    }
  }

  // Handle authentication success
  const handleAuthSuccess = () => {
    setCurrentScreen("dashboard")
    toast.success(`Welcome ${profile?.first_name || 'back'}!`)
  }

  // Onboarding Screen
  const renderOnboarding = () => (
    <div className="min-h-screen bg-gradient-to-br from-blue-50 to-indigo-100 flex items-center justify-center p-4">
      <Card className="w-full max-w-md text-center p-8">
        <div className="mb-8">
          <div className="w-20 h-20 bg-blue-600 rounded-full flex items-center justify-center mx-auto mb-4">
            <Smartphone className="w-10 h-10 text-white" />
          </div>
          <h1 className="text-3xl font-bold text-gray-900 mb-2">KSWiFi</h1>
          <p className="text-gray-600 mb-6">Virtual eSIM Data Manager</p>
          <p className="text-sm text-gray-500">
            Download data packs on WiFi, activate anywhere with eSIM
          </p>
        </div>
        
        <div className="space-y-3">
          <Button 
            className="w-full" 
            size="lg"
            onClick={() => setAuthScreen("signup")}
          >
            Get Started
          </Button>
          <Button 
            variant="outline" 
            className="w-full" 
            size="lg"
            onClick={() => setAuthScreen("signin")}
          >
            Sign In
          </Button>
        </div>
      </Card>
    </div>
  )

  // Authentication Screen
  const renderAuth = () => (
    <div className="min-h-screen bg-gradient-to-br from-blue-50 to-indigo-100 flex items-center justify-center p-4">
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
    <div className="min-h-screen bg-gradient-to-br from-blue-50 to-indigo-100">
      <div className="max-w-md mx-auto bg-white shadow-2xl min-h-screen">
        {/* Header */}
        <div className="bg-gradient-to-r from-blue-600 to-indigo-600 text-white p-6 rounded-b-3xl">
          <div className="flex justify-between items-center mb-4">
            <div>
              <h1 className="text-2xl font-bold">KSWiFi</h1>
              <p className="text-blue-100">Welcome, {userData.name.split(' ')[0]}</p>
            </div>
            <div className="flex space-x-2">
              <Button
                variant="ghost"
                size="sm"
                onClick={() => setCurrentScreen("settings")}
                className="text-white hover:bg-white/20"
              >
                <Settings className="w-5 h-5" />
              </Button>
              <Button
                variant="ghost"
                size="sm"
                onClick={handleSignOut}
                className="text-white hover:bg-white/20"
              >
                <LogOut className="w-5 h-5" />
              </Button>
            </div>
          </div>
          
          <WifiStatus 
            isConnected={userData.isWifiConnected} 
            networkName={userData.networkName} 
          />
        </div>

        {/* Data Usage */}
        <div className="p-6">
          <DataMeter 
            currentData={userData.currentData} 
            totalData={userData.totalData} 
          />
        </div>

        {/* Action Buttons */}
        <div className="px-6 pb-6">
          <div className="grid grid-cols-2 gap-4">
            <ActionButton
              icon={Download}
              label="Download Packs"
              description="On WiFi"
              onClick={handleDataPackDownload}
            />
            <ActionButton
              icon={QrCode}
              label="Scan QR"
              description="Activate eSIM"
              onClick={() => showNotification("info", "QR Scanner", "QR scanner feature coming soon!")}
            />
          </div>
        </div>

        {/* Recent Activity */}
        <div className="px-6 pb-6">
          <div className="flex justify-between items-center mb-4">
            <h2 className="text-lg font-semibold text-gray-900">Recent Activity</h2>
            <Button variant="ghost" size="sm">
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
      </div>

      {/* Data Pack Selector Modal */}
      {showDataPackSelector && (
        <DataPackSelector
          onSelect={handleDataPackSelect}
          onClose={() => setShowDataPackSelector(false)}
        />
      )}

      {/* Notification */}
      {notification.isVisible && (
        <NotificationPopup
          type={notification.type}
          title={notification.title}
          message={notification.message}
          onClose={() => setNotification(prev => ({ ...prev, isVisible: false }))}
        />
      )}
    </div>
  )

  // Settings Screen
  const renderSettings = () => (
    <div className="min-h-screen bg-gradient-to-br from-blue-50 to-indigo-100">
      <div className="max-w-md mx-auto bg-white shadow-2xl min-h-screen">
        <div className="bg-gradient-to-r from-blue-600 to-indigo-600 text-white p-6 rounded-b-3xl">
          <div className="flex items-center space-x-4">
            <Button
              variant="ghost"
              size="sm"
              onClick={() => setCurrentScreen("dashboard")}
              className="text-white hover:bg-white/20"
            >
              ←
            </Button>
            <h1 className="text-2xl font-bold">Settings</h1>
          </div>
        </div>

        <div className="p-6 space-y-6">
          {/* Profile Section */}
          <div>
            <h2 className="text-lg font-semibold mb-4">Profile</h2>
            <div className="space-y-3">
              <div className="flex items-center justify-between p-3 bg-gray-50 rounded-lg">
                <div className="flex items-center space-x-3">
                  <User className="w-5 h-5 text-gray-600" />
                  <div>
                    <p className="font-medium">{userData.name}</p>
                    <p className="text-sm text-gray-600">{userData.email}</p>
                  </div>
                </div>
              </div>
            </div>
          </div>

          {/* Security Section */}
          <div>
            <h2 className="text-lg font-semibold mb-4">Security</h2>
            <div className="space-y-3">
              <div className="flex items-center justify-between p-3 bg-gray-50 rounded-lg">
                <div className="flex items-center space-x-3">
                  <Shield className="w-5 h-5 text-gray-600" />
                  <span>Enhanced Security</span>
                </div>
                <Button
                  variant="outline"
                  size="sm"
                  onClick={() => setSecurityEnabled(!securityEnabled)}
                >
                  {securityEnabled ? "Enabled" : "Enable"}
                </Button>
              </div>
            </div>
          </div>

          {/* Support Section */}
          <div>
            <h2 className="text-lg font-semibold mb-4">Support</h2>
            <div className="space-y-3">
              <Button variant="ghost" className="w-full justify-start p-3">
                <HelpCircle className="w-5 h-5 mr-3" />
                Help Center
              </Button>
              <Button variant="ghost" className="w-full justify-start p-3">
                <Info className="w-5 h-5 mr-3" />
                About KSWiFi
              </Button>
            </div>
          </div>

          {/* Sign Out */}
          <div className="pt-6 border-t">
            <Button 
              variant="destructive" 
              className="w-full"
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

  // Loading state
  if (authLoading) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-gradient-to-br from-blue-50 to-indigo-100">
        <div className="text-center">
          <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600 mx-auto mb-4"></div>
          <p className="text-gray-600">Loading...</p>
        </div>
      </div>
    )
  }

  // Render based on authentication state
  if (!user) {
    return currentScreen === "onboarding" ? renderOnboarding() : renderAuth()
  }

  // Authenticated user screens
  return (
    <ProtectedRoute fallback={renderAuth()}>
      {currentScreen === "dashboard" && renderDashboard()}
      {currentScreen === "settings" && renderSettings()}
    </ProtectedRoute>
  )
}