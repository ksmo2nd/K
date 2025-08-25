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
  Phone,
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
  { id: 'esim', name: 'eSIM Setup', icon: Download, color: 'text-purple-500' },
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
    answer: 'Welcome to KSWiFi! To get started: 1) Create your account by signing up with your email, 2) Choose a data pack that suits your needs, 3) Download your internet session when connected to WiFi, 4) Activate your data pack and start browsing. You can also set up Face ID or Touch ID for quick access to your account.'
  },
  {
    id: '2',
    category: 'getting-started',
    question: 'What is KSWiFi and how does it work?',
    answer: 'KSWiFi is a modern mobile data management app that lets you purchase data packs, manage eSIM services, and monitor your internet usage in real-time. Our app provides secure WiFi data pack management with cross-platform support for iOS and Android devices.'
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
    answer: 'To download internet sessions: 1) Make sure you\'re connected to a stable WiFi network, 2) Go to the main dashboard, 3) Tap "Download Session", 4) Choose your preferred data pack size, 5) Wait for the download to complete. You can only download sessions when connected to WiFi for security reasons.'
  },
  {
    id: '5',
    category: 'wifi-data',
    question: 'Why can\'t I download sessions without WiFi?',
    answer: 'For security and data integrity reasons, internet sessions can only be downloaded over WiFi connections. This ensures a stable download process and prevents interruptions that could corrupt your data pack. Make sure you\'re connected to a trusted WiFi network before downloading.'
  },
  {
    id: '6',
    category: 'wifi-data',
    question: 'How do I monitor my data usage?',
    answer: 'Your data usage is displayed prominently on the main dashboard with a visual meter showing current usage vs. total data. You can view detailed usage statistics, remaining data, and usage history in the "My Sessions" section. The app provides real-time updates as you use your data.'
  },
  
  // eSIM Setup
  {
    id: '7',
    category: 'esim',
    question: 'How do I set up an eSIM?',
    answer: 'To set up your eSIM: 1) Tap "Setup eSIM" on the dashboard, 2) Generate your QR code, 3) Go to your device Settings > Cellular/Mobile Data, 4) Add Cellular Plan, 5) Scan the QR code provided by KSWiFi, 6) Follow your device\'s setup instructions. Your eSIM will be activated automatically.'
  },
  {
    id: '8',
    category: 'esim',
    question: 'Which devices support eSIM?',
    answer: 'eSIM is supported on most modern smartphones including iPhone XS and later, Google Pixel 3 and later, Samsung Galaxy S20 and later, and many other Android devices. Check your device specifications or contact your device manufacturer to confirm eSIM compatibility.'
  },
  {
    id: '9',
    category: 'esim',
    question: 'Can I use multiple eSIMs?',
    answer: 'Yes! Most modern devices support multiple eSIM profiles. You can have several KSWiFi eSIM profiles installed and switch between them as needed. Each eSIM can have its own data pack and usage tracking.'
  },
  
  // Billing & Plans
  {
    id: '10',
    category: 'billing',
    question: 'What data pack sizes are available?',
    answer: 'You can download free data packs up to 5GB at no cost. For anything exceeding 5GB, you pay ₦800 (Nigerian Naira). All data packs expire after 7 days from purchase, but your active sessions won\'t expire unless you exhaust the data you\'ve downloaded.'
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
    answer: 'Additional data beyond the free 5GB costs ₦800 (Nigerian Naira). This gives you access to larger data packs for heavy usage, streaming, or extended internet sessions. Payment is processed securely through our payment system.'
  },
  {
    id: '14',
    category: 'billing',
    question: 'How do I purchase additional data?',
    answer: 'To purchase additional data: 1) Go to the main dashboard, 2) Tap "Activate Data Pack", 3) Choose from available pack sizes, 4) Complete the secure payment process with ₦800, 5) Your new data pack will be available for download immediately after payment confirmation.'
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
    answer: 'We only collect essential information needed to provide our service: your email address, name, data usage statistics, and device information for eSIM provisioning. We never sell your personal data and only use it to improve your KSWiFi experience.'
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
    question: 'My eSIM QR code won\'t scan',
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
          
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <Button variant="outline" className="h-auto p-3 md:p-4 flex items-center space-x-2 md:space-x-3">
              <Mail className="w-4 h-4 md:w-5 md:h-5 text-primary flex-shrink-0" />
              <div className="text-left min-w-0 flex-1">
                <div className="font-semibold text-sm md:text-base">Email Support</div>
                <div className="text-xs md:text-sm text-muted-foreground truncate">support@kswifi.app</div>
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
          
          <div className="text-sm text-muted-foreground text-center pt-2">
            Response time: Usually within 2-4 hours
          </div>
        </CardContent>
      </Card>
    </div>
  )
}