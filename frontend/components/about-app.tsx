"use client"

import { Button } from '@/components/ui/button'
import { Card, CardHeader, CardTitle, CardContent } from '@/components/ui/card'
import { 
  Smartphone, 
  Wifi, 
  Shield, 
  Zap, 
  Globe, 
  Database, 
  Heart,
  Users,
  Sparkles,
  Mail,
  Phone,
  ExternalLink
} from 'lucide-react'

const features = [
  {
    icon: Shield,
    title: "Secure Authentication",
    description: "Advanced security with biometric authentication support (Face ID/Touch ID) for your peace of mind.",
    color: "text-red-500"
  },
  {
    icon: Smartphone,
    title: "Cross-Platform Mobile",
    description: "Available on both iOS and Android devices for seamless mobile experience anywhere.",
    color: "text-blue-500"
  },
  {
    icon: Wifi,
    title: "Real-Time WiFi Detection",
    description: "Smart network detection with connection monitoring and signal strength tracking.",
    color: "text-green-500"
  },
  {
    icon: Globe,
    title: "eSIM Integration",
    description: "Real eSIM provider integration with instant QR code generation and automatic activation.",
    color: "text-purple-500"
  },
  {
    icon: Database,
    title: "Data Usage Monitoring",
    description: "Real-time data consumption tracking with detailed analytics and usage insights.",
    color: "text-orange-500"
  },
  {
    icon: Zap,
    title: "Background Monitoring",
    description: "Automatic data balance checks and smart notifications for low balance alerts.",
    color: "text-yellow-500"
  }
]

export function AboutApp() {
  return (
    <div className="max-w-6xl mx-auto p-4 md:p-6 space-y-6 md:space-y-8">
      {/* Header */}
      <div className="text-center space-y-4">
        <div className="flex items-center justify-center space-x-3">
          <div className="w-12 h-12 bg-primary rounded-xl flex items-center justify-center">
            <Wifi className="w-6 h-6 text-primary-foreground" />
          </div>
          <div>
            <h1 className="text-3xl md:text-4xl font-bold text-foreground">KSWiFi</h1>
            <p className="text-muted-foreground">Version 1.0</p>
          </div>
        </div>
        
        <div className="max-w-3xl mx-auto">
          <p className="text-lg md:text-xl text-muted-foreground leading-relaxed">
            Your ultimate companion for seamless internet connectivity. Download data packs on WiFi, 
            activate anywhere with eSIM technology, and stay connected wherever life takes you.
          </p>
        </div>
      </div>

      {/* Mission Statement */}
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center text-lg md:text-xl">
            <Sparkles className="w-5 h-5 mr-2 text-primary" />
            Our Mission
          </CardTitle>
        </CardHeader>
        <CardContent>
          <p className="text-muted-foreground leading-relaxed text-sm md:text-base">
            At KSWiFi, we believe that staying connected shouldn't be complicated or expensive. 
            Our mission is to provide you with the most convenient, secure, and affordable way to 
            access the internet anywhere in the world. Whether you're traveling, working remotely, 
            or just need reliable backup connectivity, we've got you covered.
          </p>
        </CardContent>
      </Card>

      {/* Key Features */}
      <Card>
        <CardHeader>
          <CardTitle className="text-lg md:text-xl">What Makes KSWiFi Special</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4 md:gap-6">
            {features.map((feature, index) => {
              const Icon = feature.icon
              return (
                <div key={index} className="flex items-start space-x-3 p-3 md:p-4 rounded-lg bg-muted/30">
                  <div className="flex-shrink-0">
                    <Icon className={`w-6 h-6 md:w-8 md:h-8 ${feature.color}`} />
                  </div>
                  <div className="min-w-0 flex-1">
                    <h3 className="font-semibold text-foreground mb-2 text-sm md:text-base">
                      {feature.title}
                    </h3>
                    <p className="text-muted-foreground text-xs md:text-sm leading-relaxed">
                      {feature.description}
                    </p>
                  </div>
                </div>
              )
            })}
          </div>
        </CardContent>
      </Card>

      {/* App Information */}
      <Card>
        <CardHeader>
          <CardTitle className="text-lg md:text-xl">App Information</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="grid grid-cols-2 md:grid-cols-4 gap-4 md:gap-6 text-center">
            <div className="space-y-2">
              <div className="text-xl md:text-2xl font-bold text-primary">1.0</div>
              <div className="text-xs md:text-sm text-muted-foreground">Current Version</div>
            </div>
            <div className="space-y-2">
              <div className="text-xl md:text-2xl font-bold text-primary">2025</div>
              <div className="text-xs md:text-sm text-muted-foreground">Year Released</div>
            </div>
            <div className="space-y-2">
              <div className="text-xl md:text-2xl font-bold text-primary">iOS & Android</div>
              <div className="text-xs md:text-sm text-muted-foreground">Platforms</div>
            </div>
            <div className="space-y-2">
              <div className="text-xl md:text-2xl font-bold text-primary">24/7</div>
              <div className="text-xs md:text-sm text-muted-foreground">Support Available</div>
            </div>
          </div>
        </CardContent>
      </Card>

      {/* How It Works */}
      <Card>
        <CardHeader>
          <CardTitle className="text-lg md:text-xl">How KSWiFi Works</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4 md:gap-6">
            <div className="text-center space-y-3">
              <div className="w-12 h-12 mx-auto bg-primary/10 rounded-full flex items-center justify-center">
                <span className="text-primary font-bold text-lg">1</span>
              </div>
              <h3 className="font-semibold text-sm md:text-base">Download Data Packs</h3>
              <p className="text-muted-foreground text-xs md:text-sm">
                Connect to WiFi and download your data packs for offline use
              </p>
            </div>
            
            <div className="text-center space-y-3">
              <div className="w-12 h-12 mx-auto bg-primary/10 rounded-full flex items-center justify-center">
                <span className="text-primary font-bold text-lg">2</span>
              </div>
              <h3 className="font-semibold text-sm md:text-base">Activate eSIM</h3>
              <p className="text-muted-foreground text-xs md:text-sm">
                Scan the QR code to activate your eSIM on compatible devices
              </p>
            </div>
            
            <div className="text-center space-y-3">
              <div className="w-12 h-12 mx-auto bg-primary/10 rounded-full flex items-center justify-center">
                <span className="text-primary font-bold text-lg">3</span>
              </div>
              <h3 className="font-semibold text-sm md:text-base">Stay Connected</h3>
              <p className="text-muted-foreground text-xs md:text-sm">
                Enjoy seamless internet connectivity anywhere you go
              </p>
            </div>
          </div>
        </CardContent>
      </Card>

      {/* Privacy & Security */}
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center text-lg md:text-xl">
            <Shield className="w-5 h-5 mr-2 text-primary" />
            Privacy & Security
          </CardTitle>
        </CardHeader>
        <CardContent className="space-y-4">
          <p className="text-muted-foreground text-sm md:text-base">
            Your privacy and security are our top priorities. KSWiFi uses industry-standard 
            encryption and security measures to protect your data and ensure your online activities 
            remain private.
          </p>
          
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <div className="flex items-start space-x-3">
              <Shield className="w-5 h-5 text-green-500 mt-0.5 flex-shrink-0" />
              <div>
                <div className="font-semibold text-sm md:text-base">End-to-End Encryption</div>
                <div className="text-muted-foreground text-xs md:text-sm">All your data is encrypted in transit and at rest</div>
              </div>
            </div>
            
            <div className="flex items-start space-x-3">
              <Shield className="w-5 h-5 text-blue-500 mt-0.5 flex-shrink-0" />
              <div>
                <div className="font-semibold text-sm md:text-base">Biometric Authentication</div>
                <div className="text-muted-foreground text-xs md:text-sm">Secure login with Face ID, Touch ID, or fingerprint</div>
              </div>
            </div>
          </div>
        </CardContent>
      </Card>

      {/* Support & Contact */}
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center text-lg md:text-xl">
            <Users className="w-5 h-5 mr-2 text-primary" />
            Support & Community
          </CardTitle>
        </CardHeader>
        <CardContent className="space-y-4">
          <p className="text-muted-foreground text-sm md:text-base">
            Need help or have questions? Our dedicated support team is here to assist you 
            24/7. We're committed to providing you with the best possible experience.
          </p>
          
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <Button variant="outline" className="h-auto p-3 md:p-4 flex items-center space-x-2 md:space-x-3">
              <Mail className="w-4 h-4 md:w-5 md:h-5 text-primary flex-shrink-0" />
              <div className="text-left min-w-0 flex-1">
                <div className="font-semibold text-sm md:text-base">Email Support</div>
                <div className="text-xs md:text-sm text-muted-foreground">support@kswifi.app</div>
              </div>
              <ExternalLink className="w-3 h-3 md:w-4 md:h-4 flex-shrink-0" />
            </Button>
            
            <Button variant="outline" className="h-auto p-3 md:p-4 flex items-center space-x-2 md:space-x-3">
              <Phone className="w-4 h-4 md:w-5 md:h-5 text-primary flex-shrink-0" />
              <div className="text-left min-w-0 flex-1">
                <div className="font-semibold text-sm md:text-base">Phone Support</div>
                <div className="text-xs md:text-sm text-muted-foreground">Available 24/7</div>
              </div>
              <ExternalLink className="w-3 h-3 md:w-4 md:h-4 flex-shrink-0" />
            </Button>
          </div>
        </CardContent>
      </Card>

      {/* Footer */}
      <Card>
        <CardContent className="p-4 md:p-6">
          <div className="text-center space-y-3">
            <div className="flex items-center justify-center space-x-2">
              <Heart className="w-4 h-4 text-red-500" />
              <span className="text-sm md:text-base text-muted-foreground">
                Made with love for seamless connectivity
              </span>
            </div>
            
            <div className="text-xs md:text-sm text-muted-foreground">
              © 2025 KSWiFi. All rights reserved. 
              <br className="md:hidden" />
              <span className="hidden md:inline"> • </span>
              Connecting you to the world, one data pack at a time.
            </div>
          </div>
        </CardContent>
      </Card>
    </div>
  )
}