import { Wifi, WifiOff } from "lucide-react"
import { Badge } from "@/components/ui/badge"

interface WifiStatusProps {
  isConnected: boolean
  networkName?: string
}

export function WifiStatus({ isConnected, networkName }: WifiStatusProps) {
  return (
    <div className="flex items-center gap-2 p-3 rounded-lg bg-card border">
      {isConnected ? <Wifi className="w-5 h-5 text-primary" /> : <WifiOff className="w-5 h-5 text-muted-foreground" />}
      <div className="flex-1">
        <div className="text-sm font-medium">{isConnected ? "Connected to WiFi" : "No WiFi Connection"}</div>
        {networkName && <div className="text-xs text-muted-foreground">{networkName}</div>}
      </div>
      <Badge variant={isConnected ? "default" : "secondary"}>{isConnected ? "Online" : "Offline"}</Badge>
    </div>
  )
}
