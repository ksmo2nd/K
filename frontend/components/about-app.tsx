"use client"

import { Button } from '@/components/ui/button'
import { Card, CardHeader, CardTitle, CardContent } from '@/components/ui/card'
import { Badge } from '@/components/ui/badge'
import { 
  Smartphone, 
  Wifi, 
  Shield, 
  Zap, 
  Globe, 
  Database, 
  Code, 
  ExternalLink,
  Github,
  Heart,
  Users,
  Sparkles
} from 'lucide-react'

const features = [
  {
    icon: Shield,
    title: "Secure Authentication",
    description: "Industry-standard security with biometric authentication support (Face ID/Touch ID) and Supabase integration.",
    color: "text-red-500"
  },
  {
    icon: Smartphone,
    title: "Cross-Platform Mobile",
    description: "Native iOS and Android apps built with Capacitor for seamless mobile experience.",
    color: "text-blue-500"
  },
  {
    icon: Wifi,
    title: "Real-Time WiFi Detection",
    description: "Smart network detection with connection type identification and signal strength monitoring.",
    color: "text-green-500"
  },
  {
    icon: Globe,
    title: "eSIM Integration",
    description: "Real eSIM provider integration with QR code generation and automatic activation.",
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

const techStack = {
  frontend: [
    { name: "Next.js 15", description: "React framework with App Router" },
    { name: "React 19", description: "Modern UI library" },
    { name: "TypeScript", description: "Type safety and better development experience" },
    { name: "Tailwind CSS", description: "Utility-first CSS framework" },
    { name: "shadcn/ui", description: "Modern component library" }
  ],
  backend: [
    { name: "FastAPI", description: "High-performance Python web framework" },
    { name: "Supabase", description: "Database, Auth, and Real-time features" },
    { name: "PostgreSQL", description: "Primary database via Supabase" },
    { name: "Redis", description: "Background task queue and caching" },
    { name: "SQLAlchemy", description: "Async database ORM" }
  ],
  mobile: [
    { name: "Capacitor", description: "Cross-platform mobile runtime" },
    { name: "Native Biometric", description: "Face ID and Touch ID support" },
    { name: "iOS/Android", description: "Platform-specific builds" }
  ],
  infrastructure: [
    { name: "Docker", description: "Containerization for deployment" },
    { name: "Row Level Security", description: "Database-level user isolation" },
    { name: "Vercel", description: "Frontend deployment platform" },
    { name: "Render", description: "Backend API hosting" }
  ]
}

export function AboutApp() {
  return (
    <div className="max-w-6xl mx-auto p-6 space-y-8">
      {/* Header */}
      <div className="text-center space-y-4">
        <div className="flex items-center justify-center space-x-3">
          <div className="w-12 h-12 bg-primary rounded-xl flex items-center justify-center">
            <Wifi className="w-6 h-6 text-primary-foreground" />
          </div>
          <div>
            <h1 className="text-4xl font-bold text-foreground">KSWiFi</h1>
            <p className="text-muted-foreground">Version 2.0.0</p>
          </div>
        </div>
        <p className="text-xl text-muted-foreground max-w-3xl mx-auto">
          A modern mobile-first application for managing WiFi data packs and eSIM services, 
          built with cutting-edge technology for seamless user experience.
        </p>
      </div>

      {/* Key Features */}
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center">
            <Sparkles className="w-5 h-5 mr-2 text-primary" />
            Key Features
          </CardTitle>
        </CardHeader>
        <CardContent>
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
            {features.map((feature, index) => {
              const Icon = feature.icon
              return (
                <div key={index} className="space-y-3">
                  <div className="flex items-center space-x-3">
                    <Icon className={`w-6 h-6 ${feature.color}`} />
                    <h3 className="font-semibold text-foreground">{feature.title}</h3>
                  </div>
                  <p className="text-sm text-muted-foreground leading-relaxed">
                    {feature.description}
                  </p>
                </div>
              )
            })}
          </div>
        </CardContent>
      </Card>

      {/* What Makes KSWiFi Special */}
      <Card>
        <CardHeader>
          <CardTitle>What Makes KSWiFi Special</CardTitle>
        </CardHeader>
        <CardContent className="space-y-4">
          <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
            <div className="space-y-4">
              <h3 className="font-semibold text-foreground flex items-center">
                <Shield className="w-5 h-5 mr-2 text-green-500" />
                Security First
              </h3>
              <ul className="space-y-2 text-sm text-muted-foreground">
                <li>• Enterprise-grade security with Row Level Security (RLS)</li>
                <li>• Biometric authentication (Face ID, Touch ID, Fingerprint)</li>
                <li>• HTTPS encryption for all data transmission</li>
                <li>• Secure session management with data-based expiry</li>
              </ul>
            </div>
            
            <div className="space-y-4">
              <h3 className="font-semibold text-foreground flex items-center">
                <Zap className="w-5 h-5 mr-2 text-yellow-500" />
                Smart & Efficient
              </h3>
              <ul className="space-y-2 text-sm text-muted-foreground">
                <li>• Real-time network detection and monitoring</li>
                <li>• Automatic data usage tracking and analytics</li>
                <li>• Background monitoring with smart notifications</li>
                <li>• Data-based session expiry (no time limits)</li>
              </ul>
            </div>
            
            <div className="space-y-4">
              <h3 className="font-semibold text-foreground flex items-center">
                <Smartphone className="w-5 h-5 mr-2 text-blue-500" />
                Cross-Platform
              </h3>
              <ul className="space-y-2 text-sm text-muted-foreground">
                <li>• Native iOS and Android mobile apps</li>
                <li>• Progressive Web App (PWA) support</li>
                <li>• Responsive design for all screen sizes</li>
                <li>• Offline capability for essential features</li>
              </ul>
            </div>
            
            <div className="space-y-4">
              <h3 className="font-semibold text-foreground flex items-center">
                <Globe className="w-5 h-5 mr-2 text-purple-500" />
                Modern Technology
              </h3>
              <ul className="space-y-2 text-sm text-muted-foreground">
                <li>• Built with Next.js 15 and React 19</li>
                <li>• FastAPI backend for high performance</li>
                <li>• Real-time updates with Supabase</li>
                <li>• TypeScript for reliability and maintainability</li>
              </ul>
            </div>
          </div>
        </CardContent>
      </Card>

      {/* Technology Stack */}
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center">
            <Code className="w-5 h-5 mr-2 text-primary" />
            Technology Stack
          </CardTitle>
        </CardHeader>
        <CardContent>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-8">
            {Object.entries(techStack).map(([category, technologies]) => (
              <div key={category} className="space-y-4">
                <h3 className="font-semibold text-foreground capitalize">
                  {category.replace(/([A-Z])/g, ' $1').trim()}
                </h3>
                <div className="space-y-3">
                  {technologies.map((tech, index) => (
                    <div key={index} className="flex items-start space-x-3">
                      <Badge variant="secondary" className="mt-0.5">
                        {tech.name}
                      </Badge>
                      <span className="text-sm text-muted-foreground">
                        {tech.description}
                      </span>
                    </div>
                  ))}
                </div>
              </div>
            ))}
          </div>
        </CardContent>
      </Card>

      {/* App Stats */}
      <Card>
        <CardHeader>
          <CardTitle>App Information</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="grid grid-cols-2 md:grid-cols-4 gap-6 text-center">
            <div className="space-y-2">
              <div className="text-2xl font-bold text-primary">2.0.0</div>
              <div className="text-sm text-muted-foreground">Current Version</div>
            </div>
            <div className="space-y-2">
              <div className="text-2xl font-bold text-primary">2024</div>
              <div className="text-sm text-muted-foreground">Year Released</div>
            </div>
            <div className="space-y-2">
              <div className="text-2xl font-bold text-primary">iOS & Android</div>
              <div className="text-sm text-muted-foreground">Platforms</div>
            </div>
            <div className="space-y-2">
              <div className="text-2xl font-bold text-primary">24/7</div>
              <div className="text-sm text-muted-foreground">Support Available</div>
            </div>
          </div>
        </CardContent>
      </Card>

      {/* Open Source & Community */}
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center">
            <Heart className="w-5 h-5 mr-2 text-red-500" />
            Open Source & Community
          </CardTitle>
        </CardHeader>
        <CardContent className="space-y-4">
          <p className="text-muted-foreground">
            KSWiFi is built with modern open-source technologies and follows best practices 
            for security, performance, and user experience. We believe in transparency and 
            community-driven development.
          </p>
          
          <div className="flex flex-wrap gap-4">
            <Button variant="outline" className="flex items-center space-x-2">
              <Github className="w-4 h-4" />
              <span>View on GitHub</span>
              <ExternalLink className="w-3 h-3" />
            </Button>
            
            <Button variant="outline" className="flex items-center space-x-2">
              <Users className="w-4 h-4" />
              <span>Join Community</span>
              <ExternalLink className="w-3 h-3" />
            </Button>
          </div>
        </CardContent>
      </Card>

      {/* License & Credits */}
      <Card>
        <CardHeader>
          <CardTitle>License & Credits</CardTitle>
        </CardHeader>
        <CardContent className="space-y-4">
          <div className="text-sm text-muted-foreground space-y-2">
            <p>
              <strong>License:</strong> MIT License - Free to use, modify, and distribute
            </p>
            <p>
              <strong>Created with:</strong> Next.js, React, FastAPI, Supabase, and many other 
              amazing open-source technologies
            </p>
            <p>
              <strong>Special thanks:</strong> To the open-source community and all contributors 
              who make projects like this possible
            </p>
          </div>
          
          <div className="pt-4 border-t border-border text-center">
            <p className="text-sm text-muted-foreground">
              Made with <Heart className="w-4 h-4 inline text-red-500 mx-1" /> for seamless connectivity
            </p>
          </div>
        </CardContent>
      </Card>
    </div>
  )
}