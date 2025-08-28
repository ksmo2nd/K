# VPS Virtual WiFi Captive Portal Setup for KSWiFi

## 🎯 **Objective**
Create a software-defined WiFi access point on VPS that:
- ✅ Broadcasts "KSWIFI" network 
- ✅ Users scan QR codes → automatic WiFi connection
- ✅ Captive portal authenticates via FastAPI backend
- ✅ Session limits (data/time/bandwidth) enforced
- ✅ Works globally, no physical hardware needed

## 🏗️ **Architecture Overview**
```
User Phone → Scan QR → Connect to "KSWIFI" → VPS WiFi AP → Captive Portal → FastAPI Backend → Internet
```

## 📋 **Implementation Plan**

### **Phase 1: VPS Base Setup**
- Install Ubuntu 22.04 packages: `hostapd`, `dnsmasq`, `iptables`, `CoovaChilli`
- Configure network interfaces for WiFi access point mode
- Enable IP forwarding and NAT for internet access

### **Phase 2: WiFi Access Point Configuration**
- Configure `hostapd` to broadcast "KSWIFI" network
- Set up `dnsmasq` for DHCP IP assignment to connected devices
- Configure `iptables` rules for traffic routing and captive portal redirect

### **Phase 3: Captive Portal Integration**
- Install and configure `CoovaChilli` for captive portal functionality
- Integrate with existing FastAPI backend at `https://kswifi.onrender.com`
- Implement session token validation from QR codes

### **Phase 4: Backend Integration**
- Modify existing WiFi service to generate VPS-compatible session tokens
- Update database schema for VPS session tracking
- Implement authentication endpoints for captive portal

### **Phase 5: QR Code Enhancement**
- Update QR generation to include encrypted session tokens
- Ensure QR format works with automatic WiFi connection on iOS/Android
- Test QR scanning and automatic connection flow

### **Phase 6: Session Management**
- Implement data/time/bandwidth limits per session
- Auto-expire sessions based on database settings
- Real-time session monitoring and logging

### **Phase 7: Testing & Validation**
- Test QR scanning on iOS and Android devices
- Verify automatic WiFi connection and internet access
- Validate session limits and expiry functionality
- Performance and security testing

## 🛠️ **Technical Stack**
- **OS**: Ubuntu 22.04 LTS
- **WiFi AP**: hostapd (creates virtual WiFi interface)
- **DHCP**: dnsmasq (assigns IP addresses to connected devices)
- **Captive Portal**: CoovaChilli (handles authentication flow)
- **Firewall**: iptables (traffic routing and portal redirect)
- **Backend**: Existing FastAPI + Supabase integration
- **Database**: Existing Supabase tables + VPS session extensions

## 📦 **Required VPS Specifications**
- **CPU**: 1-2 vCPUs (sufficient for small-medium load)
- **RAM**: 1-2GB (for OS + services)
- **Storage**: 20GB SSD minimum
- **Network**: WiFi-capable VPS or USB WiFi adapter support
- **Provider**: Hetzner, DigitalOcean, Vultr, AWS Lightsail

## 🔄 **Integration Points**
- **Existing Backend**: `https://kswifi.onrender.com`
- **Database**: Current Supabase instance
- **QR Generation**: Existing WiFi QR service
- **Session Management**: Current session tracking system

## 🎯 **Expected User Flow**
1. **User opens KSWiFi app** → Downloads/activates data pack
2. **Generates QR code** → Contains WiFi credentials + encrypted session token
3. **Scans QR code** → Phone automatically connects to "KSWIFI" network
4. **Opens browser** → Redirected to captive portal
5. **Portal authenticates** → Validates session token with backend
6. **Grants internet access** → User browses normally with session limits
7. **Session expires** → Automatic disconnect based on data/time limits

## 🚀 **Next Steps**
Ready to begin implementation. Will start with VPS setup and work through each phase systematically, confirming success at each step and providing clear error reporting.

**Shall I proceed with Phase 1: VPS Base Setup?**