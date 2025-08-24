"use client"

import { Button } from "@/components/ui/button"
import type { LucideIcon } from "lucide-react"

interface ActionButtonProps {
  icon: LucideIcon
  label: string
  description: string
  onClick: () => void
  disabled?: boolean
  variant?: "default" | "secondary"
}

export function ActionButton({
  icon: Icon,
  label,
  description,
  onClick,
  disabled = false,
  variant = "default",
}: ActionButtonProps) {
  return (
    <Button
      onClick={onClick}
      disabled={disabled}
      variant={variant === "default" ? "default" : "secondary"}
      className="w-full h-auto p-4 flex flex-col items-center gap-2 text-left bg-primary text-primary-foreground hover:bg-primary/90"
    >
      <Icon className="w-8 h-8" />
      <div className="space-y-1">
        <div className="font-semibold">{label}</div>
        <div className="text-xs opacity-80">{description}</div>
      </div>
    </Button>
  )
}
