"use client"

import { useState } from "react"
import { Button } from "@/components/ui/button"
import { Card } from "@/components/ui/card"
import { DataMeter } from "@/components/data-meter"
import { WifiStatus } from "@/components/wifi-status"
import { ActionButton } from "@/components/action-button"
import { HistoryItem } from "@/components/history-item"
import { NotificationPopup } from "@/components/notification-popup"
import { DataPackSelector } from "@/components/data-pack-selector"
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

export default function KSWiFiApp() {
  const [currentScreen, setCurrentScreen] = useState<"onboarding" | "signin" | "signup" | "dashboard" | "settings">(
    "onboarding",
  )
  const [isSignedIn, setIsSignedIn] = useState(false)
  const [showDataPackSelector, setShowDataPackSelector] = useState(false)
  const [notification, setNotification] = useState<{
    type: "success" | "warning" | "info"
    title: string
    message: string
    isVisible: boolean
  }>({ type: "info", title: "", message: "", isVisible: false })
  const [securityEnabled, setSecurityEnabled] = useState(false)

  // Mock data
  const userData = {
    name: "Alex Johnson",
    email: "alex@example.com",
    currentData: 2.3,
    totalData: 5.0,
    isWifiConnected: true,
    networkName: "CoffeeShop_WiFi",
  }

  const recentHistory = [
    { size: "2.5 GB", date: "Dec 15, 2024", used: "2.3 GB", status: "active" as const },
    { size: "1.0 GB", date: "Dec 12, 2024", used: "1.0 GB", status: "completed" as const },
    { size: "3.0 GB", date: "Dec 10, 2024", used: "2.8 GB", status: "completed" as const },
  ]

  const showNotification = (type: "success" | "warning" | "info", title: string, message: string) => {
    setNotification({ type, title, message, isVisible: true })
  }

  const handleDataPackDownload = () => {
    if (!userData.isWifiConnected) {
      showNotification("warning", "WiFi Required", "Connect to WiFi to download packs")
      return
    }
    setShowDataPackSelector(true)
  }

  const handleDataPackSelect = (pack: { size: string; price: string }) => {
    setShowDataPackSelector(false)
    showNotification("success", "Download Started", `Downloading ${pack.size} data pack...`)

    // Simulate download completion
    setTimeout(() => {
      showNotification("success", "Download Complete", `${pack.size} data pack ready to activate`)
    }, 3000)
  }

  if (currentScreen === "onboarding") {
    return (
      <div className="min-h-screen bg-background flex flex-col items-center justify-center p-6">
        <div className="w-full max-w-sm space-y-8">
          {/* Logo and branding */}
          <div className="text-center space-y-4">
            <div className="w-20 h-20 mx-auto bg-primary rounded-2xl flex items-center justify-center">
              <Smartphone className="w-10 h-10 text-primary-foreground" />
            </div>
            <div>
              <h1 className="text-3xl font-bold text-foreground">KSWiFi</h1>
              <p className="text-muted-foreground mt-2">Download data packs on WiFi, activate anywhere with eSIM</p>
            </div>
          </div>

          {/* Features */}
          <div className="space-y-4">
            <div className="flex items-center gap-3 p-3 rounded-lg bg-card">
              <Download className="w-5 h-5 text-primary" />
              <div className="text-sm">Download data while on free WiFi</div>
            </div>
            <div className="flex items-center gap-3 p-3 rounded-lg bg-card">
              <Power className="w-5 h-5 text-primary" />
              <div className="text-sm">Activate instantly with virtual eSIM</div>
            </div>
          </div>

          <Button onClick={() => setCurrentScreen("signin")} className="w-full" size="lg">
            Get Started
          </Button>
        </div>
      </div>
    )
  }

  if (currentScreen === "signin") {
    return (
      <div className="min-h-screen bg-background flex flex-col items-center justify-center p-6">
        <div className="w-full max-w-sm space-y-6">
          <div className="text-center">
            <h2 className="text-2xl font-bold text-foreground">Welcome Back</h2>
            <p className="text-muted-foreground mt-2">Sign in to your KSWiFi account</p>
          </div>

          <div className="space-y-4">
            <div className="space-y-2">
              <label className="text-sm font-medium text-foreground">Email</label>
              <input
                type="email"
                className="w-full p-3 rounded-lg bg-input border border-border text-foreground"
                placeholder="Enter your email"
              />
            </div>
            <div className="space-y-2">
              <label className="text-sm font-medium text-foreground">Password</label>
              <input
                type="password"
                className="w-full p-3 rounded-lg bg-input border border-border text-foreground"
                placeholder="Enter your password"
              />
            </div>
          </div>

          <div className="space-y-3">
            <Button
              onClick={() => {
                setIsSignedIn(true)
                setCurrentScreen("dashboard")
              }}
              className="w-full"
              size="lg"
            >
              Sign In
            </Button>

            <div className="relative">
              <div className="absolute inset-0 flex items-center">
                <div className="w-full border-t border-border"></div>
              </div>
              <div className="relative flex justify-center text-xs uppercase">
                <span className="bg-background px-2 text-muted-foreground">Or continue with</span>
              </div>
            </div>

            <div className="grid grid-cols-2 gap-3">
              <Button variant="outline" className="w-full bg-transparent">
                Google
              </Button>
              <Button variant="outline" className="w-full bg-transparent">
                Apple
              </Button>
            </div>
          </div>

          <div className="text-center text-sm">
            <span className="text-muted-foreground">Don't have an account? </span>
            <button className="text-primary hover:underline" onClick={() => setCurrentScreen("signup")}>
              Sign up
            </button>
          </div>
        </div>
      </div>
    )
  }

  if (currentScreen === "signup") {
    return (
      <div className="min-h-screen bg-background flex flex-col items-center justify-center p-6">
        <div className="w-full max-w-sm space-y-6">
          <div className="text-center">
            <h2 className="text-2xl font-bold text-foreground">Create Account</h2>
            <p className="text-muted-foreground mt-2">Join KSWiFi and start downloading data packs</p>
          </div>

          <div className="space-y-4">
            <div className="space-y-2">
              <label className="text-sm font-medium text-foreground">Full Name</label>
              <input
                type="text"
                className="w-full p-3 rounded-lg bg-input border border-border text-foreground"
                placeholder="Enter your full name"
              />
            </div>
            <div className="space-y-2">
              <label className="text-sm font-medium text-foreground">Email</label>
              <input
                type="email"
                className="w-full p-3 rounded-lg bg-input border border-border text-foreground"
                placeholder="Enter your email"
              />
            </div>
            <div className="space-y-2">
              <label className="text-sm font-medium text-foreground">Password</label>
              <input
                type="password"
                className="w-full p-3 rounded-lg bg-input border border-border text-foreground"
                placeholder="Create a password"
              />
            </div>
            <div className="space-y-2">
              <label className="text-sm font-medium text-foreground">Confirm Password</label>
              <input
                type="password"
                className="w-full p-3 rounded-lg bg-input border border-border text-foreground"
                placeholder="Confirm your password"
              />
            </div>
          </div>

          {/* Terms and conditions */}
          <div className="flex items-start gap-2">
            <input type="checkbox" className="mt-1" />
            <p className="text-xs text-muted-foreground">
              I agree to the <span className="text-primary">Terms of Service</span> and{" "}
              <span className="text-primary">Privacy Policy</span>
            </p>
          </div>

          <div className="space-y-3">
            <Button
              onClick={() => {
                setIsSignedIn(true)
                setCurrentScreen("dashboard")
                showNotification(
                  "success",
                  "Account Created",
                  "Welcome to KSWiFi! Your account has been created successfully.",
                )
              }}
              className="w-full"
              size="lg"
            >
              Create Account
            </Button>

            <div className="relative">
              <div className="absolute inset-0 flex items-center">
                <div className="w-full border-t border-border"></div>
              </div>
              <div className="relative flex justify-center text-xs uppercase">
                <span className="bg-background px-2 text-muted-foreground">Or sign up with</span>
              </div>
            </div>

            <div className="grid grid-cols-2 gap-3">
              <Button variant="outline" className="w-full bg-transparent">
                Google
              </Button>
              <Button variant="outline" className="w-full bg-transparent">
                Apple
              </Button>
            </div>
          </div>

          <div className="text-center text-sm">
            <span className="text-muted-foreground">Already have an account? </span>
            <button className="text-primary hover:underline" onClick={() => setCurrentScreen("signin")}>
              Sign in
            </button>
          </div>
        </div>
      </div>
    )
  }

  if (currentScreen === "settings") {
    return (
      <div className="min-h-screen bg-background">
        {/* Header */}
        <div className="flex items-center justify-between p-4 border-b border-border">
          <Button variant="ghost" size="sm" onClick={() => setCurrentScreen("dashboard")}>
            ← Back
          </Button>
          <h1 className="text-lg font-semibold text-foreground">Settings</h1>
          <div className="w-16"></div>
        </div>

        <div className="p-4 space-y-6">
          {/* eSIM Setup */}
          <div className="space-y-3">
            <h2 className="text-lg font-semibold text-foreground">eSIM Setup</h2>
            <div className="space-y-2">
              <ActionButton
                icon={QrCode}
                title="Get QR Code"
                description="Scan to install eSIM profile"
                onClick={() => {}}
              />
              <ActionButton
                icon={Smartphone}
                title="Add Manually"
                description="Enter activation code"
                onClick={() => {}}
                variant="secondary"
              />
            </div>
          </div>

          {/* Security Settings */}
          <div className="space-y-3">
            <h2 className="text-lg font-semibold text-foreground">Security</h2>
            <Card className="p-4">
              <div className="flex items-center justify-between">
                <div className="flex items-center gap-3">
                  <Shield className="w-5 h-5 text-primary" />
                  <div>
                    <div className="text-sm font-medium text-foreground">Enable FaceID/PIN Lock</div>
                    <div className="text-xs text-muted-foreground">Secure app access</div>
                  </div>
                </div>
                <Button
                  variant={securityEnabled ? "default" : "outline"}
                  size="sm"
                  onClick={() => {
                    setSecurityEnabled(!securityEnabled)
                    showNotification(
                      "success",
                      securityEnabled ? "Security Disabled" : "Security Enabled",
                      securityEnabled ? "App lock has been disabled" : "App is now secured with biometric lock",
                    )
                  }}
                >
                  {securityEnabled ? "ON" : "OFF"}
                </Button>
              </div>
            </Card>
          </div>

          {/* Account Info */}
          <div className="space-y-3">
            <h2 className="text-lg font-semibold text-foreground">Account Info</h2>
            <Card className="p-4 space-y-3">
              <div className="flex justify-between">
                <span className="text-muted-foreground">Email</span>
                <span className="text-foreground">{userData.email}</span>
              </div>
              <div className="flex justify-between">
                <span className="text-muted-foreground">Last Login</span>
                <span className="text-foreground">Dec 15, 2024</span>
              </div>
              <div className="flex justify-between">
                <span className="text-muted-foreground">Device ID</span>
                <span className="text-foreground font-mono text-xs">KS-7F8A9B2C</span>
              </div>
            </Card>
          </div>

          {/* Usage History */}
          <div className="space-y-3">
            <h2 className="text-lg font-semibold text-foreground">Usage History</h2>
            <Button variant="outline" className="w-full justify-start bg-transparent" onClick={() => {}}>
              <History className="w-4 h-4 mr-2" />
              View All Downloads
            </Button>
          </div>

          {/* Support */}
          <div className="space-y-3">
            <h2 className="text-lg font-semibold text-foreground">Support & Help</h2>
            <div className="space-y-2">
              <Button variant="outline" className="w-full justify-start bg-transparent" onClick={() => {}}>
                <HelpCircle className="w-4 h-4 mr-2" />
                Contact Support
              </Button>
              <Button variant="outline" className="w-full justify-start bg-transparent" onClick={() => {}}>
                FAQ & Help
              </Button>
            </div>
            {/* App version info with icon */}
            <div className="flex items-center justify-center gap-2 text-xs text-muted-foreground mt-4">
              <Info className="w-3 h-3" />
              <span>KSWiFi v1.2.0</span>
            </div>
          </div>
        </div>
      </div>
    )
  }

  // Dashboard
  return (
    <div className="min-h-screen bg-background">
      {/* Notification popup */}
      <NotificationPopup
        type={notification.type}
        title={notification.title}
        message={notification.message}
        isVisible={notification.isVisible}
        onClose={() => setNotification((prev) => ({ ...prev, isVisible: false }))}
      />

      {/* Data pack selector modal */}
      {showDataPackSelector && (
        <DataPackSelector onSelect={handleDataPackSelect} onCancel={() => setShowDataPackSelector(false)} />
      )}

      {/* Header */}
      <div className="flex items-center justify-between p-4 border-b border-border">
        <div className="flex items-center gap-3">
          <div className="w-8 h-8 bg-primary rounded-full flex items-center justify-center">
            <User className="w-4 h-4 text-primary-foreground" />
          </div>
          <div>
            <div className="text-sm font-medium text-foreground">{userData.name}</div>
            <div className="text-xs text-muted-foreground">{userData.email}</div>
          </div>
        </div>
        <div className="flex items-center gap-2">
          <Button variant="ghost" size="sm" onClick={() => setCurrentScreen("settings")}>
            <Settings className="w-4 h-4" />
          </Button>
          <Button
            variant="ghost"
            size="sm"
            onClick={() => {
              setIsSignedIn(false)
              setCurrentScreen("onboarding")
            }}
          >
            <LogOut className="w-4 h-4" />
          </Button>
        </div>
      </div>

      <div className="p-4 space-y-6">
        {/* WiFi Status */}
        <WifiStatus isConnected={userData.isWifiConnected} networkName={userData.networkName} />

        {/* Data Meter */}
        <div className="text-center space-y-4">
          <h2 className="text-xl font-semibold text-foreground">Current Balance</h2>
          <DataMeter currentData={userData.currentData} totalData={userData.totalData} unit="GB" />
        </div>

        {/* Action Buttons */}
        <div className="grid grid-cols-1 gap-3">
          <ActionButton
            icon={Download}
            title="Download Data Pack"
            description={userData.isWifiConnected ? "Ready to download" : "Connect to WiFi first"}
            onClick={handleDataPackDownload}
            disabled={!userData.isWifiConnected}
          />
          <ActionButton
            icon={Power}
            title="Activate Data Pack"
            description="Switch to KSWiFi eSIM"
            onClick={() => showNotification("info", "Activating eSIM", "Switching to KSWiFi network...")}
            variant="secondary"
          />
        </div>

        {/* Recent History */}
        <div className="space-y-3">
          <div className="flex items-center justify-between">
            <h3 className="text-lg font-semibold text-foreground">Recent Downloads</h3>
            <Button variant="ghost" size="sm" onClick={() => setCurrentScreen("settings")}>
              View All
            </Button>
          </div>
          <div className="space-y-2">
            {recentHistory.map((item, index) => (
              <HistoryItem key={index} {...item} />
            ))}
          </div>
        </div>
      </div>
    </div>
  )
}
