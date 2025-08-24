"use client"

interface DataMeterProps {
  currentData: number
  totalData: number
  unit: "GB" | "MB"
}

export function DataMeter({ currentData, totalData, unit }: DataMeterProps) {
  const percentage = (currentData / totalData) * 100
  const circumference = 2 * Math.PI * 45 // radius of 45
  const strokeDasharray = circumference
  const strokeDashoffset = circumference - (percentage / 100) * circumference

  return (
    <div className="relative w-48 h-48 mx-auto">
      {/* Background circle */}
      <svg className="w-full h-full transform -rotate-90" viewBox="0 0 100 100">
        <circle
          cx="50"
          cy="50"
          r="45"
          stroke="currentColor"
          strokeWidth="8"
          fill="none"
          className="text-muted opacity-20"
        />
        {/* Progress circle */}
        <circle
          cx="50"
          cy="50"
          r="45"
          stroke="currentColor"
          strokeWidth="8"
          fill="none"
          strokeLinecap="round"
          strokeDasharray={strokeDasharray}
          strokeDashoffset={strokeDashoffset}
          className="text-primary transition-all duration-1000 ease-out"
          style={{
            filter: "drop-shadow(0 0 8px oklch(0.65 0.25 200))",
          }}
        />
      </svg>

      {/* Center content */}
      <div className="absolute inset-0 flex flex-col items-center justify-center">
        <div className="text-3xl font-bold text-foreground">{currentData.toFixed(1)}</div>
        <div className="text-sm text-muted-foreground">
          of {totalData} {unit}
        </div>
        <div className="text-xs text-primary mt-1">{percentage.toFixed(0)}% used</div>
      </div>
    </div>
  )
}
