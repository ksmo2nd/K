"use client"

import { Shield, ShieldAlert, ShieldCheck, AlertTriangle } from "lucide-react"
import { Badge } from "@/components/ui/badge"
import { Button } from "@/components/ui/button"
import { useAppSecurity } from "@/lib/security-context"
import { useState } from "react"

export function SecurityIndicator() {
  const { security, getSecurityRecommendations, checkSecurityCompliance } = useAppSecurity()
  const [showDetails, setShowDetails] = useState(false)

  const getSecurityIcon = () => {
    switch (security.securityLevel) {
      case 'high':
        return <ShieldCheck className="w-4 h-4 text-green-500" />
      case 'medium':
        return <Shield className="w-4 h-4 text-yellow-500" />
      case 'low':
        return <ShieldAlert className="w-4 h-4 text-red-500" />
      default:
        return <Shield className="w-4 h-4 text-muted-foreground" />
    }
  }

  const getSecurityBadgeVariant = () => {
    switch (security.securityLevel) {
      case 'high':
        return 'default' as const
      case 'medium':
        return 'secondary' as const
      case 'low':
        return 'destructive' as const
      default:
        return 'outline' as const
    }
  }

  const recommendations = getSecurityRecommendations()

  return (
    <div className="p-3 rounded-lg bg-card border">
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-2">
          {getSecurityIcon()}
          <div>
            <div className="text-sm font-medium">Security Status</div>
            <div className="text-xs text-muted-foreground">
              {security.hasValidSession ? 'Session Active' : 'No Session'}
            </div>
          </div>
        </div>
        
        <div className="flex items-center gap-2">
          <Badge variant={getSecurityBadgeVariant()}>
            {security.securityLevel.toUpperCase()}
          </Badge>
          
          {security.warnings.length > 0 && (
            <Button
              variant="ghost"
              size="sm"
              onClick={() => setShowDetails(!showDetails)}
              className="text-muted-foreground hover:text-foreground p-1"
            >
              <AlertTriangle className="w-4 h-4" />
            </Button>
          )}
        </div>
      </div>

      {showDetails && (
        <div className="mt-3 pt-3 border-t border-border">
          <div className="text-xs text-muted-foreground mb-2">Security Recommendations:</div>
          <ul className="text-xs space-y-1">
            {recommendations.map((rec, index) => (
              <li key={index} className="flex items-start gap-2">
                <span className="text-primary">•</span>
                <span>{rec}</span>
              </li>
            ))}
          </ul>
          
          <div className="mt-2 text-xs text-muted-foreground">
            {security.sessionExpiryType === 'data-based' ? (
              <div>
                Session expires when data is exhausted
                {security.dataUsagePercentage > 0 && (
                  <div className="mt-1">
                    Data used: {security.dataUsagePercentage.toFixed(1)}%
                  </div>
                )}
              </div>
            ) : (
              <div>Session active until data exhausted</div>
            )}
          </div>
        </div>
      )}
    </div>
  )
}