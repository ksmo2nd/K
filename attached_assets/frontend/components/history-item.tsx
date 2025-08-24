import { Calendar, HardDrive } from "lucide-react"
import { Card } from "@/components/ui/card"

interface HistoryItemProps {
  size: string
  date: string
  used: string
  status: "completed" | "active" | "expired"
}

export function HistoryItem({ size, date, used, status }: HistoryItemProps) {
  const statusColors = {
    completed: "text-muted-foreground",
    active: "text-primary",
    expired: "text-destructive",
  }

  return (
    <Card className="p-3">
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-3">
          <HardDrive className="w-4 h-4 text-primary" />
          <div>
            <div className="text-sm font-medium">{size}</div>
            <div className="text-xs text-muted-foreground flex items-center gap-1">
              <Calendar className="w-3 h-3" />
              {date}
            </div>
          </div>
        </div>
        <div className="text-right">
          <div className="text-xs text-muted-foreground">Used: {used}</div>
          <div className={`text-xs capitalize ${statusColors[status]}`}>{status}</div>
        </div>
      </div>
    </Card>
  )
}
