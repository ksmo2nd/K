"use client"

import { useState } from "react"
import { Button } from "@/components/ui/button"
import { Card } from "@/components/ui/card"
import { X, Download, Copy, CheckCircle, AlertCircle, Smartphone, QrCode } from "lucide-react"
import { toast } from "sonner"

interface ESIMQRPopupProps {
  isOpen: boolean
  onClose: () => void
  esimData: {
    success: boolean
    esim_id: string
    session_id?: string
    qr_code_image: string
    activation_code: string
    bundle_size_mb: number
    status: string
    manual_setup: {
      activation_code: string
      apn: string
      username: string
      password: string
      instructions: string[]
    }
    message: string
  } | null
}

export function ESIMQRPopup({ isOpen, onClose, esimData }: ESIMQRPopupProps) {
  const [activeTab, setActiveTab] = useState<'qr' | 'manual'>('qr')
  const [copied, setCopied] = useState<string | null>(null)

  console.log('🔍 POPUP DEBUG: ESIMQRPopup rendered with:', { isOpen, esimData: !!esimData })
  
  if (!isOpen || !esimData) {
    console.log('🔍 POPUP DEBUG: Popup not showing - isOpen:', isOpen, 'esimData:', !!esimData)
    return null
  }
  
  console.log('🔍 POPUP DEBUG: Popup should be visible!')

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
    try {
      const link = document.createElement('a')
      link.href = esimData.qr_code_image
      link.download = `kswifi-esim-${esimData.esim_id.slice(0, 8)}.png`
      link.click()
      toast.success("QR code downloaded!")
    } catch (error) {
      toast.error("Failed to download QR code")
    }
  }

  return (
    <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50 p-4">
      <Card className="w-full max-w-md bg-white rounded-xl shadow-2xl max-h-[90vh] overflow-y-auto">
        {/* Header */}
        <div className="flex items-center justify-between p-6 border-b">
          <div className="flex items-center gap-3">
            <div className="w-10 h-10 bg-blue-100 rounded-full flex items-center justify-center">
              <Smartphone className="w-5 h-5 text-blue-600" />
            </div>
            <div>
              <h3 className="font-semibold text-gray-900">eSIM Ready!</h3>
              <p className="text-sm text-gray-500">{esimData.bundle_size_mb / 1024}GB Data Plan</p>
            </div>
          </div>
          <Button
            variant="ghost"
            size="sm"
            onClick={onClose}
            className="text-gray-400 hover:text-gray-600"
          >
            <X className="w-4 h-4" />
          </Button>
        </div>

        {/* Success Message */}
        <div className="p-6 border-b">
          <div className="flex items-center gap-2 text-green-600 mb-2">
            <CheckCircle className="w-4 h-4" />
            <span className="text-sm font-medium">Generation Successful</span>
          </div>
          <p className="text-sm text-gray-600">{esimData.message}</p>
        </div>

        {/* Tabs */}
        <div className="border-b">
          <div className="flex">
            <button
              onClick={() => setActiveTab('qr')}
              className={`flex-1 py-3 px-4 text-sm font-medium border-b-2 transition-colors ${
                activeTab === 'qr'
                  ? 'border-blue-500 text-blue-600'
                  : 'border-transparent text-gray-500 hover:text-gray-700'
              }`}
            >
              <QrCode className="w-4 h-4 inline mr-2" />
              QR Code
            </button>
            <button
              onClick={() => setActiveTab('manual')}
              className={`flex-1 py-3 px-4 text-sm font-medium border-b-2 transition-colors ${
                activeTab === 'manual'
                  ? 'border-blue-500 text-blue-600'
                  : 'border-transparent text-gray-500 hover:text-gray-700'
              }`}
            >
              Manual Setup
            </button>
          </div>
        </div>

        {/* Content */}
        <div className="p-6">
          {activeTab === 'qr' ? (
            <div className="text-center space-y-4">
              {/* QR Code */}
              <div className="bg-white p-4 rounded-lg border-2 border-dashed border-gray-200">
                <img 
                  src={esimData.qr_code_image} 
                  alt="eSIM QR Code" 
                  className="w-48 h-48 mx-auto"
                />
              </div>
              
              {/* Instructions */}
              <div className="text-left space-y-2">
                <h4 className="font-medium text-gray-900">Setup Instructions:</h4>
                <ol className="text-sm text-gray-600 space-y-1">
                  {esimData.manual_setup.instructions.map((instruction, index) => (
                    <li key={index} className="flex gap-2">
                      <span className="text-blue-600 font-medium">{index + 1}.</span>
                      <span>{instruction}</span>
                    </li>
                  ))}
                </ol>
              </div>

              {/* Action Buttons */}
              <div className="flex gap-2 pt-2">
                <Button onClick={downloadQRCode} className="flex-1" size="sm">
                  <Download className="w-4 h-4 mr-2" />
                  Download QR
                </Button>
                <Button 
                  variant="outline" 
                  onClick={() => copyToClipboard(esimData.activation_code, 'Activation Code')}
                  className="flex-1"
                  size="sm"
                >
                  {copied === 'Activation Code' ? (
                    <CheckCircle className="w-4 h-4 mr-2 text-green-500" />
                  ) : (
                    <Copy className="w-4 h-4 mr-2" />
                  )}
                  Copy Code
                </Button>
              </div>
            </div>
          ) : (
            <div className="space-y-4">
              {/* Manual Setup Details */}
              <div className="space-y-3">
                <div>
                  <label className="block text-xs font-medium text-gray-500 uppercase tracking-wide mb-1">
                    Activation Code
                  </label>
                  <div className="flex items-center gap-2">
                    <code className="flex-1 p-2 bg-gray-50 rounded text-xs font-mono break-all">
                      {esimData.manual_setup.activation_code}
                    </code>
                    <Button
                      variant="ghost"
                      size="sm"
                      onClick={() => copyToClipboard(esimData.manual_setup.activation_code, 'Activation Code')}
                    >
                      {copied === 'Activation Code' ? (
                        <CheckCircle className="w-4 h-4 text-green-500" />
                      ) : (
                        <Copy className="w-4 h-4" />
                      )}
                    </Button>
                  </div>
                </div>

                <div className="grid grid-cols-2 gap-3">
                  <div>
                    <label className="block text-xs font-medium text-gray-500 uppercase tracking-wide mb-1">
                      APN
                    </label>
                    <div className="flex items-center gap-2">
                      <code className="flex-1 p-2 bg-gray-50 rounded text-xs">
                        {esimData.manual_setup.apn}
                      </code>
                      <Button
                        variant="ghost"
                        size="sm"
                        onClick={() => copyToClipboard(esimData.manual_setup.apn, 'APN')}
                      >
                        {copied === 'APN' ? (
                          <CheckCircle className="w-4 h-4 text-green-500" />
                        ) : (
                          <Copy className="w-4 h-4" />
                        )}
                      </Button>
                    </div>
                  </div>

                  <div>
                    <label className="block text-xs font-medium text-gray-500 uppercase tracking-wide mb-1">
                      Username
                    </label>
                    <div className="flex items-center gap-2">
                      <code className="flex-1 p-2 bg-gray-50 rounded text-xs">
                        {esimData.manual_setup.username}
                      </code>
                      <Button
                        variant="ghost"
                        size="sm"
                        onClick={() => copyToClipboard(esimData.manual_setup.username, 'Username')}
                      >
                        {copied === 'Username' ? (
                          <CheckCircle className="w-4 h-4 text-green-500" />
                        ) : (
                          <Copy className="w-4 h-4" />
                        )}
                      </Button>
                    </div>
                  </div>
                </div>

                <div>
                  <label className="block text-xs font-medium text-gray-500 uppercase tracking-wide mb-1">
                    Password
                  </label>
                  <div className="flex items-center gap-2">
                    <code className="flex-1 p-2 bg-gray-50 rounded text-xs">
                      {esimData.manual_setup.password}
                    </code>
                    <Button
                      variant="ghost"
                      size="sm"
                      onClick={() => copyToClipboard(esimData.manual_setup.password, 'Password')}
                    >
                      {copied === 'Password' ? (
                        <CheckCircle className="w-4 h-4 text-green-500" />
                      ) : (
                        <Copy className="w-4 h-4" />
                      )}
                    </Button>
                  </div>
                </div>
              </div>

              {/* Manual Instructions */}
              <div className="pt-2 border-t">
                <h4 className="font-medium text-gray-900 mb-2">Manual Setup Steps:</h4>
                <ol className="text-sm text-gray-600 space-y-1">
                  {esimData.manual_setup.instructions.map((instruction, index) => (
                    <li key={index} className="flex gap-2">
                      <span className="text-blue-600 font-medium">{index + 1}.</span>
                      <span>{instruction}</span>
                    </li>
                  ))}
                </ol>
              </div>
            </div>
          )}
        </div>

        {/* Footer */}
        <div className="px-6 py-4 bg-gray-50 border-t">
          <div className="flex items-center gap-2 text-amber-600">
            <AlertCircle className="w-4 h-4" />
            <span className="text-xs">Keep this information safe. You'll need it to set up your eSIM.</span>
          </div>
        </div>
      </Card>
    </div>
  )
}