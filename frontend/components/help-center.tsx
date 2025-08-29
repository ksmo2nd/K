"use client"

import { useState } from 'react'
import { Button } from '@/components/ui/button'
import { Card, CardHeader, CardTitle, CardContent } from '@/components/ui/card'
import { Input } from '@/components/ui/input'
import { 
  HelpCircle, 
  Search, 
  ChevronRight, 
  ChevronDown, 
  Wifi, 
  Smartphone, 
  CreditCard, 
  Shield, 
  Download,
  Settings,
  MessageCircle,
  Mail,
  ExternalLink
} from 'lucide-react'

interface FAQItem {
  id: string
  question: string
  answer: string
  category: string
}

interface HelpCategory {
  id: string
  name: string
  icon: any
  color: string
}

const helpCategories: HelpCategory[] = [
  { id: 'getting-started', name: 'Getting Started', icon: Smartphone, color: 'text-blue-500' },
  { id: 'wifi-data', name: 'WiFi & Data', icon: Wifi, color: 'text-green-500' },
  { id: 'connect', name: 'KSWiFi Connect', icon: Download, color: 'text-purple-500' },
  { id: 'billing', name: 'Billing & Plans', icon: CreditCard, color: 'text-orange-500' },
  { id: 'security', name: 'Security & Privacy', icon: Shield, color: 'text-red-500' },
  { id: 'troubleshooting', name: 'Troubleshooting', icon: Settings, color: 'text-gray-500' },
]

const faqData: FAQItem[] = [
  // Getting Started
  {
    id: '1',
    category: 'getting-started',
    question: 'How do I get started with KSWiFi?',
    answer: 'Welcome to KSWiFi! To get started: 1) Create your account by signing up with your email, 2) Choose a data pack that suits your needs, 3) Download your internet session when connected to WiFi, 4) Generate your KSWiFi Connect code, 5) Scan the QR code to install your internet profile, 6) Enjoy global internet access anywhere! You can also set up Face ID or Touch ID for quick access.'
  },
  {
    id: '2',
    category: 'getting-started',
    question: 'What is KSWiFi and how does it work?',
    answer: 'KSWiFi is a revolutionary global internet access platform that gives you affordable internet anywhere in the world. Download internet sessions on WiFi, then use KSWiFi Connect to access the internet globally without expensive roaming charges. Our VPN-based system works on any device and provides secure, fast internet access using your pre-purchased data allowances.'
  },
  {
    id: '3',
    category: 'getting-started',
    question: 'Do I need to create an account?',
    answer: 'Yes, you need to create a secure account to access all KSWiFi features. This allows us to sync your data packs, usage history, and preferences across all your devices. We use industry-standard security measures to protect your personal information.'
  },
  
  // WiFi & Data
  {
    id: '4',
    category: 'wifi-data',
    question: 'How do I download internet sessions?',
    answer: 'To download internet sessions: 1) Connect to a trusted WiFi network, 2) Go to the dashboard, 3) Tap "Download Session", 4) Choose your data pack size (1GB, 3GB, 5GB, etc.), 5) Wait for the download to complete. Once downloaded, you can generate a KSWiFi Connect code to use this data anywhere in the world!'
  },
  {
    id: '5',
    category: 'wifi-data',
    question: 'Why can\'t I download sessions without WiFi?',
    answer: 'Internet sessions must be downloaded over WiFi for several important reasons: 1) Security - WiFi provides a more secure environment for downloading sensitive internet data, 2) Stability - WiFi connections are more stable for large downloads, 3) Cost savings - Downloading over WiFi doesn\'t use your mobile data, 4) Speed - WiFi typically provides faster download speeds. Once downloaded, you can use KSWiFi Connect anywhere!'
  },
  {
    id: '6',
    category: 'wifi-data',
    question: 'How do I monitor my data usage?',
    answer: 'Your data usage is displayed prominently on the main dashboard with a visual meter showing current usage vs. total data. You can view detailed usage statistics, remaining data, and usage history in the "My Sessions" section. The app provides real-time updates as you use your data.'
  },
  
  // KSWiFi Connect Setup
  {
    id: '7',
    category: 'connect',
    question: 'How do I set up KSWiFi Connect?',
    answer: 'To set up KSWiFi Connect: 1) Tap "Setup Connect" on the dashboard, 2) Generate your Connect Code, 3) Scan the QR code with your phone camera, 4) Tap "Add" when prompted to install the VPN profile, 5) Enable "KSWiFi Connect" in your VPN settings, 6) Enjoy instant global internet access using your session data!'
  },
  {
    id: '8',
    category: 'connect',
    question: 'Which devices support KSWiFi Connect?',
    answer: 'KSWiFi Connect works on all modern smartphones including iPhone (iOS 10+) and Android devices (5.0+). It uses VPN technology that is built into every phone, so no additional apps are required. Simply scan the QR code and your phone will automatically install the connection profile.'
  },
  {
    id: '9',
    category: 'connect',
    question: 'Can I use multiple Connect profiles?',
    answer: 'Yes! You can have multiple KSWiFi Connect profiles for different sessions and data allowances. Each profile tracks its own usage and limits. You can switch between profiles in your phone\'s VPN settings as needed.'
  },
  {
    id: '9a',
    category: 'connect',
    question: 'What makes KSWiFi Connect different from regular VPNs?',
    answer: 'KSWiFi Connect is specifically designed for affordable global internet access using your pre-purchased data sessions. Unlike regular VPNs that just hide your location, KSWiFi Connect provides actual internet connectivity anywhere in the world at a fraction of the cost of international roaming or local SIM cards.'
  },
  {
    id: '9b',
    category: 'connect',
    question: 'How fast is KSWiFi Connect internet?',
    answer: 'KSWiFi Connect provides high-speed internet suitable for streaming, social media, video calls, and web browsing. Speed depends on your data pack size and server location, but you can expect smooth performance for TikTok, Instagram, YouTube, WhatsApp, and other popular apps. Perfect for staying connected while traveling!'
  },
  {
    id: '9c',
    category: 'connect',
    question: 'Can I use KSWiFi Connect for streaming and video calls?',
    answer: 'Absolutely! KSWiFi Connect provides full internet access, so you can stream Netflix, YouTube, TikTok, make WhatsApp video calls, FaceTime calls, Zoom meetings, and use any internet-dependent app just like you would with regular WiFi or mobile data. It\'s perfect for staying entertained and connected while traveling.'
  },
  {
    id: '9d',
    category: 'connect',
    question: 'Does KSWiFi Connect work in all countries?',
    answer: 'Yes! KSWiFi Connect works globally in any country where you have basic internet connectivity (even slow hotel WiFi or public WiFi). Once connected, you get full-speed internet access using your data sessions. It\'s perfect for international travel, remote work, or accessing content from anywhere in the world.'
  },
  
  // Billing & Plans
  {
    id: '10',
    category: 'billing',
    question: 'What data pack sizes are available?',
    answer: 'You can download free data packs up to 5GB at no cost. For anything exceeding 5GB, you pay ₦800. All data packs expire after 7 days from purchase, but your active sessions won\'t expire unless you exhaust the data you\'ve downloaded.'
  },
  {
    id: '11',
    category: 'billing',
    question: 'When do my data packs expire?',
    answer: 'Data packs expire 7 days after purchase, but your active internet sessions won\'t expire unless you completely exhaust the data you\'ve downloaded. This means once you download a session, you have full control over when to use it - it won\'t disappear due to time limits.'
  },
  {
    id: '12',
    category: 'billing',
    question: 'Is there free data available?',
    answer: 'Yes! You can download up to 5GB of data completely free. This is perfect for basic browsing, messaging, and light usage. If you need more than 5GB, you can purchase additional data for ₦800.'
  },
  {
    id: '13',
    category: 'billing',
    question: 'How much does additional data cost?',
    answer: 'Additional data beyond the free 5GB costs ₦800. This gives you access to larger data packs for heavy usage, streaming, or extended internet sessions. Payment is processed securely through our payment system.'
  },
  {
    id: '14',
    category: 'billing',
    question: 'How do I purchase additional data?',
    answer: 'To purchase additional data: 1) Go to dashboard, 2) Tap "Activate Data Pack", 3) Choose pack size, 4) Pay ₦800, 5) Download immediately after payment.'
  },
  
  // Security & Privacy
  {
    id: '15',
    category: 'security',
    question: 'How do I enable Face ID or Touch ID?',
    answer: 'To enable biometric authentication: 1) Sign in with your email and password, 2) Check the "Enable Face ID/Touch ID for future sign-ins" option, 3) Complete your sign-in, 4) Your biometric data will be securely saved for future logins. You can disable this feature anytime in your device settings.'
  },
  {
    id: '16',
    category: 'security',
    question: 'Is my data secure?',
    answer: 'Yes! We use industry-standard security measures including HTTPS encryption, secure authentication via Supabase, Row Level Security (RLS) for database protection, and biometric authentication support. Your personal data and usage information are protected with enterprise-grade security.'
  },
  {
    id: '17',
    category: 'security',
    question: 'What information do you collect?',
    answer: 'We only collect essential information needed to provide our service: your email address, name, data usage statistics, and device information for KSWiFi Connect provisioning. We never sell your personal data and only use it to improve your KSWiFi experience.'
  },
  
  // Troubleshooting
  {
    id: '18',
    category: 'troubleshooting',
    question: 'My app shows "No Internet Connection" but I\'m connected',
    answer: 'This usually indicates a connectivity issue. Try: 1) Check if you\'re connected to a working WiFi network, 2) Restart the app, 3) Check your device\'s internet settings, 4) Try connecting to a different WiFi network, 5) Contact support if the issue persists.'
  },
  {
    id: '19',
    category: 'troubleshooting',
    question: 'My KSWiFi Connect QR code won\'t scan',
    answer: 'If your QR code won\'t scan: 1) Ensure your device camera has permission to access the camera, 2) Clean your camera lens, 3) Make sure you\'re in good lighting, 4) Try generating a new QR code from the app, 5) You can also manually enter the activation code if scanning fails.'
  },
  {
    id: '20',
    category: 'troubleshooting',
    question: 'I can\'t download internet sessions',
    answer: 'If you can\'t download sessions: 1) Ensure you\'re connected to WiFi (cellular connections won\'t work), 2) Check that you have sufficient storage space, 3) Verify your account has active data packs, 4) Try restarting the app, 5) Contact support if downloads continue to fail.'
  }
]

export function HelpCenter() {
  const [selectedCategory, setSelectedCategory] = useState<string | null>(null)
  const [expandedFAQ, setExpandedFAQ] = useState<string | null>(null)
  const [searchQuery, setSearchQuery] = useState('')

  const filteredFAQs = faqData.filter(faq => {
    const matchesSearch = searchQuery === '' || 
      faq.question.toLowerCase().includes(searchQuery.toLowerCase()) ||
      faq.answer.toLowerCase().includes(searchQuery.toLowerCase())
    
    const matchesCategory = selectedCategory === null || faq.category === selectedCategory
    
    return matchesSearch && matchesCategory
  })

  const getCategoryCount = (categoryId: string) => {
    return faqData.filter(faq => faq.category === categoryId).length
  }

  return (
    <div className="max-w-4xl mx-auto p-6 space-y-6">
      {/* Header */}
      <div className="text-center space-y-4">
        <div className="flex items-center justify-center">
          <HelpCircle className="w-8 h-8 text-primary mr-3" />
          <h1 className="text-3xl font-bold text-foreground">Help Center</h1>
        </div>
        <p className="text-muted-foreground text-lg">
          Find answers to common questions about KSWiFi
        </p>
      </div>

      {/* Search */}
      <Card>
        <CardContent className="p-6">
          <div className="relative">
            <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 text-muted-foreground w-5 h-5" />
            <Input
              type="text"
              placeholder="Search for help articles..."
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              className="pl-10 text-lg h-12"
            />
          </div>
        </CardContent>
      </Card>

      {/* Categories */}
      {!searchQuery && (
        <Card>
          <CardHeader>
            <CardTitle>Browse by Category</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
              {helpCategories.map((category) => {
                const Icon = category.icon
                return (
                  <Button
                    key={category.id}
                    variant={selectedCategory === category.id ? "default" : "outline"}
                    className="h-auto p-3 md:p-4 flex flex-col items-center space-y-2"
                    onClick={() => setSelectedCategory(
                      selectedCategory === category.id ? null : category.id
                    )}
                  >
                    <Icon className={`w-6 h-6 md:w-8 md:h-8 ${category.color}`} />
                    <div className="text-center">
                      <div className="font-semibold text-xs md:text-sm">{category.name}</div>
                      <div className="text-xs md:text-sm text-muted-foreground">
                        {getCategoryCount(category.id)} articles
                      </div>
                    </div>
                  </Button>
                )
              })}
            </div>
          </CardContent>
        </Card>
      )}

      {/* FAQ Items */}
      <div className="space-y-4">
        {filteredFAQs.length > 0 ? (
          <>
            {selectedCategory && (
              <div className="flex items-center justify-between">
                <h2 className="text-xl font-semibold">
                  {helpCategories.find(cat => cat.id === selectedCategory)?.name} 
                  <span className="text-muted-foreground ml-2">
                    ({filteredFAQs.length} articles)
                  </span>
                </h2>
                <Button
                  variant="ghost"
                  onClick={() => setSelectedCategory(null)}
                  className="text-muted-foreground"
                >
                  Show All Categories
                </Button>
              </div>
            )}
            
            {filteredFAQs.map((faq) => (
              <Card key={faq.id}>
                <CardContent className="p-0">
                  <Button
                    variant="ghost"
                    className="w-full p-4 md:p-6 h-auto justify-between text-left"
                    onClick={() => setExpandedFAQ(
                      expandedFAQ === faq.id ? null : faq.id
                    )}
                  >
                    <span className="font-medium text-foreground pr-2 md:pr-4 text-sm md:text-base">
                      {faq.question}
                    </span>
                    {expandedFAQ === faq.id ? (
                      <ChevronDown className="w-5 h-5 text-muted-foreground flex-shrink-0" />
                    ) : (
                      <ChevronRight className="w-5 h-5 text-muted-foreground flex-shrink-0" />
                    )}
                  </Button>
                  
                  {expandedFAQ === faq.id && (
                    <div className="px-4 md:px-6 pb-4 md:pb-6 pt-0">
                      <div className="text-muted-foreground leading-relaxed text-sm md:text-base">
                        {faq.answer}
                      </div>
                    </div>
                  )}
                </CardContent>
              </Card>
            ))}
          </>
        ) : (
          <Card>
            <CardContent className="p-12 text-center">
              <Search className="w-12 h-12 text-muted-foreground mx-auto mb-4" />
              <h3 className="text-lg font-semibold mb-2">No results found</h3>
              <p className="text-muted-foreground">
                Try adjusting your search terms or browse by category
              </p>
            </CardContent>
          </Card>
        )}
      </div>

      {/* Contact Support */}
      <Card className="border-primary/20">
        <CardHeader>
          <CardTitle className="flex items-center">
            <MessageCircle className="w-5 h-5 mr-2 text-primary" />
            Still need help?
          </CardTitle>
        </CardHeader>
        <CardContent className="space-y-4">
          <p className="text-muted-foreground">
            Can't find what you're looking for? Our support team is here to help.
          </p>
          
          <Button variant="outline" className="h-auto p-3 md:p-4 flex items-center space-x-2 md:space-x-3 mx-auto max-w-md">
            <Mail className="w-4 h-4 md:w-5 md:h-5 text-primary flex-shrink-0" />
            <div className="text-left min-w-0 flex-1">
              <div className="font-semibold text-sm md:text-base">Email Support</div>
              <div className="text-xs md:text-sm text-muted-foreground truncate">support@kswifi.app</div>
            </div>
            <ExternalLink className="w-3 h-3 md:w-4 md:h-4 flex-shrink-0" />
          </Button>
          
          <div className="text-sm text-muted-foreground text-center pt-2">
            Response time: Usually within 2-4 hours
          </div>
        </CardContent>
      </Card>
    </div>
  )
}