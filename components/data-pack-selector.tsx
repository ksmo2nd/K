"use client"

import { useState } from "react"
import { Button } from "@/components/ui/button"
import { Card } from "@/components/ui/card"
import { Download, Check } from "lucide-react"

interface DataPackOption {
  size: string
  price: string
  popular?: boolean
}

interface DataPackSelectorProps {
  onSelect: (pack: DataPackOption) => void
  onCancel: () => void
}

export function DataPackSelector({ onSelect, onCancel }: DataPackSelectorProps) {
  const [selectedPack, setSelectedPack] = useState<DataPackOption | null>(null)

  const dataPacks: DataPackOption[] = [
    { size: "1 GB", price: "$2.99" },
    { size: "5 GB", price: "$9.99", popular: true },
    { size: "10 GB", price: "$17.99" },
  ]

  return (
    <div className="fixed inset-0 bg-black/50 backdrop-blur-sm z-50 flex items-center justify-center p-4">
      <div className="w-full max-w-sm bg-background rounded-lg p-6 space-y-6">
        <div className="text-center">
          <h2 className="text-xl font-semibold text-foreground">Select Data Pack</h2>
          <p className="text-sm text-muted-foreground mt-1">Choose how much data to download</p>
        </div>

        <div className="space-y-3">
          {dataPacks.map((pack) => (
            <Card
              key={pack.size}
              className={`p-4 cursor-pointer transition-all relative ${
                selectedPack?.size === pack.size
                  ? "border-primary bg-primary/5"
                  : "border-border hover:border-primary/50"
              }`}
              onClick={() => setSelectedPack(pack)}
            >
              {pack.popular && (
                <div className="absolute -top-2 left-4 bg-primary text-primary-foreground text-xs px-2 py-1 rounded">
                  Popular
                </div>
              )}
              <div className="flex items-center justify-between">
                <div>
                  <div className="font-medium text-foreground">{pack.size}</div>
                  <div className="text-sm text-muted-foreground">{pack.price}</div>
                </div>
                {selectedPack?.size === pack.size && <Check className="w-5 h-5 text-primary" />}
              </div>
            </Card>
          ))}
        </div>

        <div className="flex gap-3">
          <Button variant="outline" onClick={onCancel} className="flex-1 bg-transparent">
            Cancel
          </Button>
          <Button onClick={() => selectedPack && onSelect(selectedPack)} disabled={!selectedPack} className="flex-1">
            <Download className="w-4 h-4 mr-2" />
            Download
          </Button>
        </div>
      </div>
    </div>
  )
}
