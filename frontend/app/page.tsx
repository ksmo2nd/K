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
import { apiService } from "@/lib/api"
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

interface UserData {
  id: number
  email: string
  first_name: string
  last_name: string
  phone_number?: string
  data_packs?: Array<{
    id: number
    size_gb: number
    used_gb: number
    purchase_date: string
    status: string
  }>
}

export default function KSWiFiApp() {
  const [currentScreen, setCurrentScreen] = useState<"onboarding" | "signin" | "signup" | "dashboard" | "settings">(
    "onboarding",
  )
  const [isSignedIn, setIsSignedIn] = useState(false)
  const [isLoading, setIsLoading] = useState(false)
  const [currentUser, setCurrentUser] = useState<UserData | null>(null)
  const [showDataPackSelector, setShowDataPackSelector] = useState(false)
  const [notification, setNotification] = useState<{
    type: "success" | "warning" | "info"
    title: string
    message: string
    isVisible: boolean
  }>({ type: "info", title: "", message: "", isVisible: false })
  const [securityEnabled, setSecurityEnabled] = useState(false)

  // Check for existing auth token on mount
  useEffect(() => {
    checkAuthStatus()
  }, [])

  const checkAuthStatus = async () => {
    const token = localStorage.getItem('access_token')
    if (token) {
      try {
        const user = await apiService.getCurrentUser()
        setCurrentUser(user)
        setIsSignedIn(true)
        setCurrentScreen("dashboard")
      } catch (error) {
        localStorage.removeItem('access_token')
        setCurrentScreen("onboarding")
      }
    }
  }

  // Real user data from API (fallback to mock if not signed in)
  const userData = currentUser ? {
    name: `${currentUser.first_name} ${currentUser.last_name}`,
    email: currentUser.email,
    currentData: 0, // Will be populated from data packs
    totalData: 0, // Will be populated from data packs
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

  // Real history data from API (fallback to mock if not signed in)  
  const recentHistory = [
    { size: "No data packs", date: "Sign in to view", used: "0 GB", status: "completed" as const },
  ]

  const showNotification = (type: "success" | "warning" | "info", title: string, message: string) => {
    setNotification({ type, title, message, isVisible: true })
  }

  const handleSignIn = async (email: string, password: string) => {
    setIsLoading(true)
    try {
      const response = await apiService.login(email, password)
      setCurrentUser(response.user)
      setIsSignedIn(true)
      setCurrentScreen("dashboard")
      showNotification("success", "Welcome Back!", `Signed in as ${response.user.first_name}`)
    } catch (error: any) {
      showNotification("warning", "Sign In Failed", error.message || "Please check your credentials")
    } finally {
      setIsLoading(false)
    }
  }

  const handleSignUp = async (userData: {
    email: string
    password: string
    first_name: string
    last_name: string
    phone_number?: string
  }) => {
    setIsLoading(true)
    try {
      const response = await apiService.signup(userData)
      setCurrentUser(response.user)
      setIsSignedIn(true)
      setCurrentScreen("dashboard")
      showNotification("success", "Account Created!", `Welcome ${response.user.first_name}!`)
    } catch (error: any) {
      showNotification("warning", "Sign Up Failed", error.message || "Please try again")
    } finally {
      setIsLoading(false)
    }
  }

  const handleSignOut = async () => {
    try {
      await apiService.logout()
    } catch (error) {
      console.error('Logout error:', error)
    } finally {
      setCurrentUser(null)
      setIsSignedIn(false)
      setCurrentScreen("onboarding")
      localStorage.removeItem('access_token')
      showNotification("info", "Signed Out", "Come back soon!")
    }
  }

  const handleDataPackDownload = () => {
    if (!userData.isWifiConnected) {
      showNotification("warning", "WiFi Required", "Connect to WiFi to download packs")
      return
    }
    if (!isSignedIn) {
      showNotification("warning", "Sign In Required", "Please sign in to purchase data packs")
      setCurrentScreen("signin")
      return
    }
    setShowDataPackSelector(true)
  }

  const handleDataPackSelect = async (pack: { size: string; price: string }) => {
    setShowDataPackSelector(false)
    
    if (!isSignedIn || !currentUser) {
      showNotification("warning", "Sign In Required", "Please sign in to purchase data packs")
      return
    }

    setIsLoading(true)
    try {
      // Extract size from string like "5 GB" -> 5
      const sizeGB = parseFloat(pack.size.replace(/[^\d.]/g, ''))
      
      await apiService.createDataPack({
        name: `${pack.size} Data Pack`,
        total_data_mb: sizeGB * 1024, // Convert GB to MB
        price: parseFloat(pack.price.replace(/[^\d.]/g, '')),
        expires_at: new Date(Date.now() + 30 * 24 * 60 * 60 * 1000).toISOString() // 30 days from now
      })
      
      showNotification("success", "Download Started", `Downloading ${pack.size} data pack...`)
      
      // Refresh user data to show new pack
      const updatedUser = await apiService.getCurrentUser()
      setCurrentUser(updatedUser)
      
      setTimeout(() => {
        showNotification("success", "Download Complete", `${pack.size} data pack ready to activate`)
      }, 3000)
    } catch (error: any) {
      showNotification("warning", "Purchase Failed", error.message || "Please try again")
    } finally {
      setIsLoading(false)
    }
  }

  const renderOnboarding = () => (
    <div className="min-h-screen bg-gradient-to-br from-blue-50 to-cyan-50 flex items-center justify-center p-4">
      <Card className="w-full max-w-md p-8 text-center">
        <div className="mb-8">
          <div className="w-20 h-20 bg-blue-100 rounded-full flex items-center justify-center mx-auto mb-4">
            <Smartphone className="w-10 h-10 text-blue-600" />
          </div>
          <h1 className="text-2xl font-bold text-gray-900 mb-2">Welcome to KSWiFi</h1>
          <p className="text-gray-600">Download data packs on WiFi, activate anywhere with eSIM</p>
        </div>

        <div className="space-y-4 mb-8">
          <div className="flex items-center space-x-3 text-left">
            <Download className="w-5 h-5 text-blue-600 flex-shrink-0" />
            <span className="text-sm text-gray-700">Download data packs over WiFi</span>
          </div>
          <div className="flex items-center space-x-3 text-left">
            <QrCode className="w-5 h-5 text-blue-600 flex-shrink-0" />
            <span className="text-sm text-gray-700">Get instant eSIM activation codes</span>
          </div>
          <div className="flex items-center space-x-3 text-left">
            <Shield className="w-5 h-5 text-blue-600 flex-shrink-0" />
            <span className="text-sm text-gray-700">Secure, encrypted data management</span>
          </div>
        </div>

        <div className="space-y-3">
          <Button
            onClick={() => setCurrentScreen("signup")}
            className="w-full bg-blue-600 hover:bg-blue-700"
            disabled={isLoading}
          >
            Get Started
          </Button>
          <Button 
            variant="outline" 
            onClick={() => setCurrentScreen("signin")}
            className="w-full"
            disabled={isLoading}
          >
            I Already Have an Account
          </Button>
        </div>
      </Card>
    </div>
  )

  const [signinFormData, setSigninFormData] = useState({ email: '', password: '' })
  
  const renderSignIn = () => {

    return (
      <div className="min-h-screen bg-gradient-to-br from-blue-50 to-cyan-50 flex items-center justify-center p-4">
        <Card className="w-full max-w-md p-8">
          <div className="text-center mb-8">
            <div className="w-16 h-16 bg-blue-100 rounded-full flex items-center justify-center mx-auto mb-4">
              <User className="w-8 h-8 text-blue-600" />
            </div>
            <h2 className="text-2xl font-bold text-gray-900 mb-2">Welcome Back</h2>
            <p className="text-gray-600">Sign in to your KSWiFi account</p>
          </div>

          <form onSubmit={(e) => {
            e.preventDefault()
            handleSignIn(signinFormData.email, signinFormData.password)
          }} className="space-y-4">
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">Email</label>
              <input
                type="email"
                required
                className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
                value={signinFormData.email}
                onChange={(e) => setSigninFormData({...signinFormData, email: e.target.value})}
                placeholder="Enter your email"
              />
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">Password</label>
              <input
                type="password"
                required
                className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
                value={signinFormData.password}
                onChange={(e) => setSigninFormData({...signinFormData, password: e.target.value})}
                placeholder="Enter your password"
              />
            </div>
            <Button 
              type="submit" 
              className="w-full bg-blue-600 hover:bg-blue-700"
              disabled={isLoading}
            >
              {isLoading ? "Signing In..." : "Sign In"}
            </Button>
          </form>

          <div className="mt-6 text-center">
            <button
              onClick={() => setCurrentScreen("signup")}
              className="text-blue-600 hover:text-blue-800 text-sm"
              disabled={isLoading}
            >
              Don't have an account? Sign Up
            </button>
          </div>
          <div className="mt-2 text-center">
            <button
              onClick={() => setCurrentScreen("onboarding")}
              className="text-gray-500 hover:text-gray-700 text-sm"
              disabled={isLoading}
            >
              ← Back
            </button>
          </div>
        </Card>
      </div>
    )
  }

  const [signupFormData, setSignupFormData] = useState({
    email: '',
    password: '',
    first_name: '',
    last_name: '',
    phone_number: ''
  })
  
  const renderSignUp = () => {

    return (
      <div className="min-h-screen bg-gradient-to-br from-blue-50 to-cyan-50 flex items-center justify-center p-4">
        <Card className="w-full max-w-md p-8">
          <div className="text-center mb-8">
            <div className="w-16 h-16 bg-blue-100 rounded-full flex items-center justify-center mx-auto mb-4">
              <User className="w-8 h-8 text-blue-600" />
            </div>
            <h2 className="text-2xl font-bold text-gray-900 mb-2">Create Account</h2>
            <p className="text-gray-600">Join KSWiFi to get started</p>
          </div>

          <form onSubmit={(e) => {
            e.preventDefault()
            handleSignUp(signupFormData)
          }} className="space-y-4">
            <div className="grid grid-cols-2 gap-4">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">First Name</label>
                <input
                  type="text"
                  required
                  className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
                  value={signupFormData.first_name}
                  onChange={(e) => setSignupFormData({...signupFormData, first_name: e.target.value})}
                  placeholder="First name"
                />
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">Last Name</label>
                <input
                  type="text"
                  required
                  className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
                  value={signupFormData.last_name}
                  onChange={(e) => setSignupFormData({...signupFormData, last_name: e.target.value})}
                  placeholder="Last name"
                />
              </div>
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">Email</label>
              <input
                type="email"
                required
                className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
                value={signupFormData.email}
                onChange={(e) => setSignupFormData({...signupFormData, email: e.target.value})}
                placeholder="Enter your email"
              />
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">Phone (Optional)</label>
              <input
                type="tel"
                className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
                value={signupFormData.phone_number}
                onChange={(e) => setSignupFormData({...signupFormData, phone_number: e.target.value})}
                placeholder="Phone number"
              />
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">Password</label>
              <input
                type="password"
                required
                className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
                value={signupFormData.password}
                onChange={(e) => setSignupFormData({...signupFormData, password: e.target.value})}
                placeholder="Create a password"
              />
            </div>
            <Button 
              type="submit" 
              className="w-full bg-blue-600 hover:bg-blue-700"
              disabled={isLoading}
            >
              {isLoading ? "Creating Account..." : "Create Account"}
            </Button>
          </form>

          <div className="mt-6 text-center">
            <button
              onClick={() => setCurrentScreen("signin")}
              className="text-blue-600 hover:text-blue-800 text-sm"
              disabled={isLoading}
            >
              Already have an account? Sign In
            </button>
          </div>
          <div className="mt-2 text-center">
            <button
              onClick={() => setCurrentScreen("onboarding")}
              className="text-gray-500 hover:text-gray-700 text-sm"
              disabled={isLoading}
            >
              ← Back
            </button>
          </div>
        </Card>
      </div>
    )
  }

  const renderDashboard = () => (
    <div className="min-h-screen bg-gray-50">
      {/* Header */}
      <div className="bg-white shadow-sm border-b border-gray-200 p-4">
        <div className="flex items-center justify-between">
          <div className="flex items-center space-x-3">
            <div className="w-10 h-10 bg-blue-100 rounded-full flex items-center justify-center">
              <Smartphone className="w-5 h-5 text-blue-600" />
            </div>
            <div>
              <h1 className="text-lg font-semibold text-gray-900">KSWiFi</h1>
              <p className="text-sm text-gray-500">Welcome, {userData.name}</p>
            </div>
          </div>
          <div className="flex items-center space-x-2">
            <Button variant="ghost" size="sm" onClick={() => setCurrentScreen("settings")}>
              <Settings className="w-4 h-4" />
            </Button>
            <Button variant="ghost" size="sm" onClick={handleSignOut}>
              <LogOut className="w-4 h-4" />
            </Button>
          </div>
        </div>
      </div>

      {/* Content */}
      <div className="p-4 space-y-6">
        {/* Data Usage */}
        <DataMeter currentData={userData.currentData} totalData={userData.totalData} unit="GB" />

        {/* WiFi Status */}
        <WifiStatus isConnected={userData.isWifiConnected} networkName={userData.networkName} />

        {/* Action Buttons */}
        <div className="grid grid-cols-2 gap-4">
          <ActionButton
            icon={Download}
            title="Download Data"
            description="Get data packs"
            onClick={handleDataPackDownload}
            disabled={isLoading}
          />
          <ActionButton
            icon={QrCode}
            title="eSIM Setup"
            description="QR & manual setup"
            onClick={() => showNotification("info", "eSIM Setup", "Feature available after data pack purchase")}
          />
        </div>

        {/* Recent Activity */}
        <div>
          <h2 className="text-lg font-semibold text-gray-900 mb-4 flex items-center">
            <History className="w-5 h-5 mr-2" />
            Recent Activity
          </h2>
          <div className="space-y-3">
            {recentHistory.map((item, index) => (
              <HistoryItem key={index} {...item} />
            ))}
          </div>
        </div>
      </div>

      {/* Data Pack Selector Modal */}
      {showDataPackSelector && (
        <DataPackSelector
          onCancel={() => setShowDataPackSelector(false)}
          onSelect={handleDataPackSelect}
        />
      )}
    </div>
  )

  const renderSettings = () => (
    <div className="min-h-screen bg-gray-50">
      {/* Header */}
      <div className="bg-white shadow-sm border-b border-gray-200 p-4">
        <div className="flex items-center justify-between">
          <div className="flex items-center space-x-3">
            <Button variant="ghost" size="sm" onClick={() => setCurrentScreen("dashboard")}>
              ←
            </Button>
            <h1 className="text-lg font-semibold text-gray-900">Settings</h1>
          </div>
        </div>
      </div>

      {/* Content */}
      <div className="p-4 space-y-6">
        {/* Account Info */}
        <Card className="p-4">
          <h3 className="font-semibold text-gray-900 mb-3 flex items-center">
            <User className="w-5 h-5 mr-2" />
            Account Information
          </h3>
          <div className="space-y-2 text-sm">
            <div className="flex justify-between">
              <span className="text-gray-600">Name:</span>
              <span className="text-gray-900">{userData.name}</span>
            </div>
            <div className="flex justify-between">
              <span className="text-gray-600">Email:</span>
              <span className="text-gray-900">{userData.email}</span>
            </div>
            <div className="flex justify-between">
              <span className="text-gray-600">Total Data:</span>
              <span className="text-gray-900">{userData.totalData} GB</span>
            </div>
          </div>
        </Card>

        {/* Security */}
        <Card className="p-4">
          <h3 className="font-semibold text-gray-900 mb-3 flex items-center">
            <Shield className="w-5 h-5 mr-2" />
            Security & Privacy
          </h3>
          <div className="space-y-4">
            <div className="flex items-center justify-between">
              <div>
                <div className="text-sm font-medium text-gray-900">Enhanced Security</div>
                <div className="text-xs text-gray-600">Additional protection for your account</div>
              </div>
              <Button
                variant={securityEnabled ? "default" : "outline"}
                size="sm"
                onClick={() => {
                  setSecurityEnabled(!securityEnabled)
                  showNotification(
                    "success",
                    securityEnabled ? "Security Disabled" : "Security Enabled",
                    securityEnabled
                      ? "Enhanced security has been turned off"
                      : "Your account now has enhanced security protection",
                  )
                }}
              >
                {securityEnabled ? "Enabled" : "Enable"}
              </Button>
            </div>
          </div>
        </Card>

        {/* Support */}
        <Card className="p-4">
          <h3 className="font-semibold text-gray-900 mb-3 flex items-center">
            <HelpCircle className="w-5 h-5 mr-2" />
            Help & Support
          </h3>
          <div className="space-y-3">
            <button
              onClick={() => showNotification("info", "Help Center", "Visit our help center for guides and FAQs")}
              className="w-full text-left p-3 rounded-lg hover:bg-gray-50 transition-colors"
            >
              <div className="text-sm font-medium text-gray-900">Help Center</div>
              <div className="text-xs text-gray-600">Guides, FAQs, and tutorials</div>
            </button>
            <button
              onClick={() =>
                showNotification("info", "Contact Support", "Our support team will respond within 24 hours")
              }
              className="w-full text-left p-3 rounded-lg hover:bg-gray-50 transition-colors"
            >
              <div className="text-sm font-medium text-gray-900">Contact Support</div>
              <div className="text-xs text-gray-600">Get help from our team</div>
            </button>
          </div>
        </Card>

        {/* About */}
        <Card className="p-4">
          <h3 className="font-semibold text-gray-900 mb-3 flex items-center">
            <Info className="w-5 h-5 mr-2" />
            About KSWiFi
          </h3>
          <div className="space-y-2 text-sm text-gray-600">
            <div>Version 1.0.0</div>
            <div>© 2024 KSWiFi. All rights reserved.</div>
            <div>Virtual eSIM data management platform</div>
          </div>
        </Card>

        {/* Sign Out */}
        <Button
          variant="outline"
          onClick={handleSignOut}
          className="w-full text-red-600 border-red-300 hover:bg-red-50"
          disabled={isLoading}
        >
          <LogOut className="w-4 h-4 mr-2" />
          Sign Out
        </Button>
      </div>
    </div>
  )

  return (
    <div className="relative">
      {currentScreen === "onboarding" && renderOnboarding()}
      {currentScreen === "signin" && renderSignIn()}
      {currentScreen === "signup" && renderSignUp()}
      {currentScreen === "dashboard" && renderDashboard()}
      {currentScreen === "settings" && renderSettings()}

      {/* Notification */}
      <NotificationPopup
        type={notification.type}
        title={notification.title}
        message={notification.message}
        isVisible={notification.isVisible}
        onClose={() => setNotification((prev) => ({ ...prev, isVisible: false }))}
      />
    </div>
  )
}