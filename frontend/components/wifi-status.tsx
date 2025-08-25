import { Wifi, WifiOff, Smartphone, Monitor, Signal } from "lucide-react"
import { Badge } from "@/components/ui/badge"
import { useWiFiStatus } from "@/hooks/use-wifi-status"

interface WifiStatusProps {
  // Props are now optional since we get real data from the hook
  isConnected?: boolean
  networkName?: string
}

export function WifiStatus({ isConnected: propIsConnected, networkName: propNetworkName }: WifiStatusProps) {
  // Use real WiFi status from hook, fallback to props for compatibility
  const realWiFiStatus = useWiFiStatus()
  
  const isConnected = propIsConnected !== undefined ? propIsConnected : realWiFiStatus.isConnected
  const networkName = propNetworkName !== undefined ? propNetworkName : realWiFiStatus.networkName
  const connectionType = realWiFiStatus.connectionType
  const signalStrength = realWiFiStatus.signalStrength
  const isOnline = realWiFiStatus.isOnline

  const getConnectionIcon = () => {
    if (!isConnected || !isOnline) return <WifiOff className="w-5 h-5 text-muted-foreground" />
    
    switch (connectionType) {
      case 'wifi':
        return <Wifi className="w-5 h-5 text-primary" />
      case 'cellular':
        return <Smartphone className="w-5 h-5 text-primary" />
      case 'ethernet':
        return <Monitor className="w-5 h-5 text-primary" />
      default:
        return <Signal className="w-5 h-5 text-primary" />
    }
  }

  const getConnectionText = () => {
    if (!isConnected || !isOnline) return "No Internet Connection"
    
    switch (connectionType) {
      case 'wifi':
        return "Connected via WiFi"
      case 'cellular':
        return "Connected via Cellular"
      case 'ethernet':
        return "Connected via Ethernet"
      default:
        return "Connected to Internet"
    }
  }

  const getSignalBars = () => {
    if (!signalStrength || !isConnected) return null
    
    return (
      <div className="flex items-center gap-1">
        {[1, 2, 3, 4].map((bar) => (
          <div
            key={bar}
            className={`w-1 h-3 rounded-sm ${
              bar <= signalStrength 
                ? 'bg-primary' 
                : 'bg-muted-foreground/30'
            }`}
          />
        ))}
      </div>
    )
  }

  return (
    <div className="flex items-center gap-2 p-3 rounded-lg bg-card border">
      {getConnectionIcon()}
      <div className="flex-1">
        <div className="text-sm font-medium">{getConnectionText()}</div>
        {networkName && (
          <div className="text-xs text-muted-foreground flex items-center gap-2">
            {networkName}
            {getSignalBars()}
          </div>
        )}
        {!isOnline && (
          <div className="text-xs text-destructive">Check your internet connection</div>
        )}
      </div>
      <Badge variant={isConnected && isOnline ? "default" : "secondary"}>
        {isConnected && isOnline ? "Online" : "Offline"}
      </Badge>
    </div>
  )
}
