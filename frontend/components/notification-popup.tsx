"use client"

import { useEffect } from "react"
import { CheckCircle, AlertTriangle, Wifi, X } from "lucide-react"
import { Button } from "@/components/ui/button"

interface NotificationPopupProps {
  type: "success" | "warning" | "info"
  title: string
  message: string
  isVisible: boolean
  onClose: () => void
  autoClose?: boolean
  duration?: number
}

export function NotificationPopup({
  type,
  title,
  message,
  isVisible,
  onClose,
  autoClose = true,
  duration = 3000,
}: NotificationPopupProps) {
  useEffect(() => {
    if (isVisible && autoClose) {
      const timer = setTimeout(() => {
        onClose()
      }, duration)
      return () => clearTimeout(timer)
    }
  }, [isVisible, autoClose, duration, onClose])

  if (!isVisible) return null

  const getIcon = () => {
    switch (type) {
      case "success":
        return <CheckCircle className="w-5 h-5 text-green-400" />
      case "warning":
        return <AlertTriangle className="w-5 h-5 text-yellow-400" />
      case "info":
        return <Wifi className="w-5 h-5 text-blue-400" />
    }
  }

  const getBgColor = () => {
    switch (type) {
      case "success":
        return "bg-green-900/20 border-green-500/30"
      case "warning":
        return "bg-yellow-900/20 border-yellow-500/30"
      case "info":
        return "bg-blue-900/20 border-blue-500/30"
    }
  }

  return (
    <div className="fixed top-4 left-4 right-4 z-50 animate-in slide-in-from-top-2">
      <div className={`p-4 rounded-lg border backdrop-blur-sm ${getBgColor()}`}>
        <div className="flex items-start gap-3">
          {getIcon()}
          <div className="flex-1 space-y-1">
            <h4 className="text-sm font-medium text-foreground">{title}</h4>
            <p className="text-xs text-muted-foreground">{message}</p>
          </div>
          <Button variant="ghost" size="sm" onClick={onClose} className="h-6 w-6 p-0">
            <X className="w-3 h-3" />
          </Button>
        </div>
      </div>
    </div>
  )
}
