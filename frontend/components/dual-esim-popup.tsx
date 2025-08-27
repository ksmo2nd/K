"use client"

import { useState } from "react"
import { Button } from "@/components/ui/button"
import { Card } from "@/components/ui/card"
import { X, Download, Copy, CheckCircle, AlertCircle, Smartphone, QrCode, Wifi, Lock, Globe } from "lucide-react"
import { toast } from "sonner"

interface DualESIMPopupProps {
  isOpen: boolean
  onClose: () => void
  esimData: {
    success: boolean
    data: {
      user_id: string
      session_id: string
      bundle_size_mb: number
      options: Array<{
        type: 'public_wifi' | 'private_osmo'
        access_level: 'public' | 'private'
        title: string
        description: string
        qr_code_image: string
        setup_instructions: string[]
        // Public WiFi specific
        captive_portal_url?: string
        network_name?: string
        access_token?: string
        // Private eSIM specific
        activation_code?: string
        profile_id?: string
        iccid?: string
        smdp_server?: string
      }>
      summary: {
        total_options: number
        has_public_access: boolean
        has_private_access: boolean
        private_access_available: boolean
        bundle_size_mb: number
      }
    }
  } | null
}

export function DualESIMPopup({ isOpen, onClose, esimData }: DualESIMPopupProps) {
  const [activeOption, setActiveOption] = useState<number>(0)
  const [copied, setCopied] = useState<string | null>(null)

  console.log('🔍 DUAL eSIM POPUP: Rendered with:', { isOpen, esimData: !!esimData })
  
  if (!isOpen || !esimData || !esimData.success) {
    return null
  }

  const { data } = esimData
  const currentOption = data.options[activeOption]

  const copyToClipboard = async (text: string, label: string) => {
    try {
      await navigator.clipboard.writeText(text)
      setCopied(label)
      toast.success(`${label} copied to clipboard!`)
      setTimeout(() => setCopied(null), 2000)
    } catch (error) {
      toast.error("Failed to copy to clipboard")
    }
  }

  const downloadQRCode = () => {
    if (!currentOption.qr_code_image) return
    
    const link = document.createElement('a')
    link.href = currentOption.qr_code_image
    link.download = `kswifi-${currentOption.type}-${data.bundle_size_mb}mb.png`
    document.body.appendChild(link)
    link.click()
    document.body.removeChild(link)
    toast.success("QR code downloaded!")
  }

  const openCaptivePortal = () => {
    if (currentOption.captive_portal_url) {
      window.open(currentOption.captive_portal_url, '_blank')
      toast.success("Opening captive portal...")
    }
  }

  return (
    <div className="fixed inset-0 bg-black/50 backdrop-blur-sm flex items-center justify-center z-50 p-4">
      <div className="bg-white rounded-2xl shadow-2xl max-w-2xl w-full max-h-[90vh] overflow-y-auto">
        {/* Header */}
        <div className="sticky top-0 bg-white border-b p-6 rounded-t-2xl flex items-center justify-between">
          <div>
            <h2 className="text-2xl font-bold text-gray-900 flex items-center gap-2">
              <QrCode className="w-6 h-6 text-blue-600" />
              KSWiFi eSIM Options
            </h2>
            <p className="text-gray-600 mt-1">
              {data.bundle_size_mb}MB • {data.summary.total_options} option{data.summary.total_options > 1 ? 's' : ''} available
            </p>
          </div>
          <Button 
            variant="ghost" 
            size="sm" 
            onClick={onClose}
            className="text-gray-400 hover:text-gray-600"
          >
            <X className="w-5 h-5" />
          </Button>
        </div>

        {/* Option Tabs */}
        {data.options.length > 1 && (
          <div className="border-b bg-gray-50">
            <div className="flex">
              {data.options.map((option, index) => (
                <button
                  key={index}
                  onClick={() => setActiveOption(index)}
                  className={`flex-1 p-4 text-center transition-colors ${
                    activeOption === index
                      ? 'bg-white border-b-2 border-blue-600 text-blue-600 font-medium'
                      : 'text-gray-600 hover:text-gray-900'
                  }`}
                >
                  <div className="flex items-center justify-center gap-2">
                    {option.type === 'public_wifi' ? (
                      <Wifi className="w-4 h-4" />
                    ) : (
                      <Lock className="w-4 h-4" />
                    )}
                    {option.access_level === 'public' ? 'Public WiFi' : 'Private eSIM'}
                  </div>
                </button>
              ))}
            </div>
          </div>
        )}

        {/* Content */}
        <div className="p-6">
          {/* Option Header */}
          <div className="text-center mb-6">
            <div className="flex items-center justify-center gap-2 mb-2">
              {currentOption.type === 'public_wifi' ? (
                <div className="w-12 h-12 bg-green-100 rounded-full flex items-center justify-center">
                  <Globe className="w-6 h-6 text-green-600" />
                </div>
              ) : (
                <div className="w-12 h-12 bg-blue-100 rounded-full flex items-center justify-center">
                  <Lock className="w-6 h-6 text-blue-600" />
                </div>
              )}
            </div>
            <h3 className="text-xl font-semibold text-gray-900">{currentOption.title}</h3>
            <p className="text-gray-600 mt-1">{currentOption.description}</p>
          </div>

          {/* QR Code */}
          <div className="text-center mb-6">
            <div className="inline-block p-4 bg-white border-2 border-gray-200 rounded-xl shadow-sm">
              <img 
                src={currentOption.qr_code_image} 
                alt={`${currentOption.type} QR Code`}
                className="w-48 h-48 mx-auto"
              />
            </div>
          </div>

          {/* Action Buttons */}
          <div className="flex gap-2 mb-6">
            <Button onClick={downloadQRCode} className="flex-1" size="sm">
              <Download className="w-4 h-4 mr-2" />
              Download QR
            </Button>
            
            {currentOption.type === 'public_wifi' && currentOption.captive_portal_url && (
              <Button onClick={openCaptivePortal} variant="outline" className="flex-1" size="sm">
                <Wifi className="w-4 h-4 mr-2" />
                Open Portal
              </Button>
            )}
            
            {currentOption.activation_code && (
              <Button
                onClick={() => copyToClipboard(currentOption.activation_code!, 'Activation Code')}
                variant="outline"
                className="flex-1"
                size="sm"
              >
                {copied === 'Activation Code' ? (
                  <CheckCircle className="w-4 h-4 mr-2 text-green-600" />
                ) : (
                  <Copy className="w-4 h-4 mr-2" />
                )}
                Copy Code
              </Button>
            )}
          </div>

          {/* Technical Details */}
          {currentOption.type === 'public_wifi' && (
            <Card className="p-4 bg-green-50 border-green-200 mb-6">
              <h4 className="font-medium text-green-900 mb-2 flex items-center gap-2">
                <Wifi className="w-4 h-4" />
                WiFi Network Details
              </h4>
              <div className="space-y-2 text-sm text-green-800">
                <div className="flex justify-between">
                  <span>Network Name:</span>
                  <span className="font-medium">{currentOption.network_name}</span>
                </div>
                <div className="flex justify-between">
                  <span>Access Type:</span>
                  <span className="font-medium">Open (Captive Portal)</span>
                </div>
                <div className="flex justify-between">
                  <span>Data Bundle:</span>
                  <span className="font-medium">{data.bundle_size_mb}MB</span>
                </div>
              </div>
            </Card>
          )}

          {currentOption.type === 'private_osmo' && (
            <Card className="p-4 bg-blue-50 border-blue-200 mb-6">
              <h4 className="font-medium text-blue-900 mb-2 flex items-center gap-2">
                <Lock className="w-4 h-4" />
                eSIM Profile Details
              </h4>
              <div className="space-y-2 text-sm text-blue-800">
                <div className="flex justify-between">
                  <span>ICCID:</span>
                  <span className="font-mono text-xs">{currentOption.iccid}</span>
                </div>
                <div className="flex justify-between">
                  <span>SM-DP+ Server:</span>
                  <span className="font-medium">{currentOption.smdp_server}</span>
                </div>
                <div className="flex justify-between">
                  <span>Data Bundle:</span>
                  <span className="font-medium">{data.bundle_size_mb}MB</span>
                </div>
                <div className="flex justify-between">
                  <span>Access Level:</span>
                  <span className="font-medium text-blue-600">Private</span>
                </div>
              </div>
            </Card>
          )}

          {/* Setup Instructions */}
          <div className="space-y-4">
            <h4 className="font-medium text-gray-900 flex items-center gap-2">
              <Smartphone className="w-4 h-4" />
              Setup Instructions
            </h4>
            <div className="bg-gray-50 rounded-lg p-4">
              <div className="space-y-2 text-sm text-gray-700">
                {currentOption.setup_instructions.map((instruction, index) => (
                  <div 
                    key={index} 
                    className={`${
                      instruction.startsWith('📱') || instruction.startsWith('⚠️') || instruction.startsWith('🔧') 
                        ? 'font-medium text-gray-800 mt-3 first:mt-0' 
                        : instruction === '' 
                          ? 'h-2' 
                          : 'ml-4'
                    }`}
                  >
                    {instruction}
                  </div>
                ))}
              </div>
            </div>
          </div>

          {/* Success Message */}
          <div className="mt-6 p-4 bg-green-50 border border-green-200 rounded-lg">
            <div className="flex items-start gap-2">
              <CheckCircle className="w-5 h-5 text-green-600 mt-0.5" />
              <div>
                <p className="text-green-900 font-medium">eSIM Options Generated Successfully!</p>
                <p className="text-green-700 text-sm mt-1">
                  Choose your preferred connection method and follow the setup instructions above.
                </p>
              </div>
            </div>
          </div>
        </div>

        {/* Footer */}
        <div className="border-t p-6 bg-gray-50 rounded-b-2xl">
          <div className="flex items-center justify-between text-sm text-gray-600">
            <span>Session: {data.session_id.slice(0, 8)}...</span>
            <span>{data.bundle_size_mb}MB Bundle</span>
          </div>
        </div>
      </div>
    </div>
  )
}