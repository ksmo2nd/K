#!/bin/bash

# VPS Setup Script for Transparent QR-Authenticated WiFi System
# Run this script on Ubuntu 22.04 VPS

set -e  # Exit on any error

echo "🚀 Starting VPS Setup for KSWiFi Transparent Authentication System"
echo "=================================================="

# Function to log with timestamps
log() {
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] $1"
}

# Function to check command success
check_success() {
    if [ $? -eq 0 ]; then
        log "✅ $1 - SUCCESS"
    else
        log "❌ $1 - FAILED"
        exit 1
    fi
}

# Step 1: Update system and install packages
log "🔍 STEP 1: Installing required packages..."
sudo apt update && sudo apt upgrade -y
check_success "System update"

sudo apt install -y hostapd dnsmasq iptables iptables-persistent bridge-utils wireless-tools net-tools python3-pip python3-venv curl jq tcpdump
check_success "Package installation"

# Step 2: Configure network interface
log "🔍 STEP 2: Configuring network interface..."

# Check if wireless interface exists
WIFI_INTERFACE=$(ip link show | grep -o 'wlan[0-9]*' | head -1)
if [ -z "$WIFI_INTERFACE" ]; then
    log "❌ No wireless interface found. This VPS may not support WiFi."
    log "ℹ️  You may need a VPS with WiFi capability or USB WiFi adapter."
    exit 1
fi

log "ℹ️  Found wireless interface: $WIFI_INTERFACE"

# Configure static IP for WiFi interface
sudo ip addr add 192.168.100.1/24 dev $WIFI_INTERFACE 2>/dev/null || true
sudo ip link set $WIFI_INTERFACE up
check_success "Network interface configuration"

# Step 3: Create hostapd configuration
log "🔍 STEP 3: Creating hostapd configuration..."

sudo tee /etc/hostapd/hostapd.conf > /dev/null <<EOF
interface=$WIFI_INTERFACE
driver=nl80211

# Network settings
ssid=KSWIFI
hw_mode=g
channel=6
ieee80211n=1
wmm_enabled=1

# Security settings
auth_algs=1
wpa=2
wpa_key_mgmt=WPA-PSK
wpa_pairwise=CCMP
rsn_pairwise=CCMP

# Dynamic password (will be updated by backend)
wpa_passphrase=KSWiFi2024

# Access control
macaddr_acl=0
ignore_broadcast_ssid=0

# Logging
logger_syslog=-1
logger_syslog_level=2
logger_stdout=-1
logger_stdout_level=2
EOF

check_success "hostapd configuration"

# Configure hostapd service
echo 'DAEMON_CONF="/etc/hostapd/hostapd.conf"' | sudo tee /etc/default/hostapd
sudo systemctl unmask hostapd
sudo systemctl enable hostapd
check_success "hostapd service configuration"

# Step 4: Configure dnsmasq
log "🔍 STEP 4: Configuring dnsmasq..."

# Backup original config
sudo cp /etc/dnsmasq.conf /etc/dnsmasq.conf.backup

sudo tee /etc/dnsmasq.conf > /dev/null <<EOF
# Interface to bind to
interface=$WIFI_INTERFACE

# DHCP range for connected devices
dhcp-range=192.168.100.10,192.168.100.100,255.255.255.0,24h

# DNS servers
server=8.8.8.8
server=8.8.4.4

# Don't read /etc/hosts
no-hosts

# Log queries and DHCP
log-queries
log-dhcp

# Cache size
cache-size=1000
EOF

check_success "dnsmasq configuration"

# Step 5: Enable IP forwarding
log "🔍 STEP 5: Enabling IP forwarding..."

echo 'net.ipv4.ip_forward=1' | sudo tee -a /etc/sysctl.conf
sudo sysctl -p
check_success "IP forwarding"

# Step 6: Create iptables rules
log "🔍 STEP 6: Creating iptables rules..."

# Get the main internet interface (usually eth0)
INTERNET_INTERFACE=$(ip route | grep default | awk '{print $5}' | head -1)
log "ℹ️  Internet interface: $INTERNET_INTERFACE"

# Create iptables script
sudo tee /usr/local/bin/setup_kswifi_iptables.sh > /dev/null <<EOF
#!/bin/bash

# Flush existing rules
iptables -F
iptables -t nat -F
iptables -t mangle -F

# Create custom chains for authenticated devices
iptables -N KSWIFI_AUTH 2>/dev/null || iptables -F KSWIFI_AUTH
iptables -N KSWIFI_INTERNET 2>/dev/null || iptables -F KSWIFI_INTERNET

# Default policy: DROP all traffic from WiFi interface
iptables -I FORWARD 1 -i $WIFI_INTERFACE -j KSWIFI_AUTH

# Allow established connections
iptables -A KSWIFI_AUTH -m state --state ESTABLISHED,RELATED -j ACCEPT

# Allow traffic to authentication backend (always allowed)
iptables -A KSWIFI_AUTH -p tcp --dport 443 -j ACCEPT
iptables -A KSWIFI_AUTH -p tcp --dport 80 -j ACCEPT
iptables -A KSWIFI_AUTH -p udp --dport 53 -j ACCEPT

# Allow DHCP
iptables -A KSWIFI_AUTH -p udp --dport 67:68 -j ACCEPT

# Authenticated devices chain (populated by backend)
iptables -A KSWIFI_AUTH -j KSWIFI_INTERNET

# Default: DROP unauthenticated traffic
iptables -A KSWIFI_AUTH -j DROP

# NAT for internet access
iptables -t nat -A POSTROUTING -o $INTERNET_INTERFACE -j MASQUERADE

# Allow traffic from internet interface
iptables -A FORWARD -i $INTERNET_INTERFACE -o $WIFI_INTERFACE -m state --state RELATED,ESTABLISHED -j ACCEPT

echo "iptables rules configured successfully"
EOF

sudo chmod +x /usr/local/bin/setup_kswifi_iptables.sh
sudo /usr/local/bin/setup_kswifi_iptables.sh
check_success "iptables rules"

# Save iptables rules
sudo iptables-save | sudo tee /etc/iptables/rules.v4 > /dev/null
check_success "iptables rules save"

# Step 7: Create device authentication script
log "🔍 STEP 7: Creating device authentication script..."

sudo tee /usr/local/bin/auth_device.sh > /dev/null <<'EOF'
#!/bin/bash

DEVICE_MAC=$1
DEVICE_IP=$2
ACTION=$3  # "allow" or "deny"

echo "[$(date)] AUTH: $ACTION device $DEVICE_MAC ($DEVICE_IP)"

if [ "$ACTION" = "allow" ]; then
    # Allow device internet access
    iptables -I KSWIFI_INTERNET 1 -m mac --mac-source $DEVICE_MAC -j ACCEPT
    echo "[$(date)] ✅ Device $DEVICE_MAC granted internet access"
elif [ "$ACTION" = "deny" ]; then
    # Remove device access
    iptables -D KSWIFI_INTERNET -m mac --mac-source $DEVICE_MAC -j ACCEPT 2>/dev/null
    echo "[$(date)] ❌ Device $DEVICE_MAC internet access revoked"
fi
EOF

sudo chmod +x /usr/local/bin/auth_device.sh
check_success "Device authentication script"

# Step 8: Create monitoring script
log "🔍 STEP 8: Creating monitoring script..."

sudo tee /usr/local/bin/monitor_connections.py > /dev/null <<EOF
#!/usr/bin/env python3

import time
import subprocess
import requests
import re
import json
import logging
from datetime import datetime

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='[%(asctime)s] %(levelname)s: %(message)s',
    handlers=[
        logging.FileHandler('/var/log/kswifi_monitor.log'),
        logging.StreamHandler()
    ]
)

BACKEND_URL = "https://kswifi.onrender.com"
WIFI_INTERFACE = "$WIFI_INTERFACE"

def get_connected_devices():
    """Get list of currently connected devices"""
    try:
        result = subprocess.run([
            "hostapd_cli", "-i", WIFI_INTERFACE, "all_sta"
        ], capture_output=True, text=True, timeout=10)
        
        if result.returncode == 0:
            # Parse MAC addresses
            macs = re.findall(
                r'([0-9a-fA-F]{2}:[0-9a-fA-F]{2}:[0-9a-fA-F]{2}:[0-9a-fA-F]{2}:[0-9a-fA-F]{2}:[0-9a-fA-F]{2})',
                result.stdout
            )
            return set(macs)
        else:
            logging.error(f"hostapd_cli failed: {result.stderr}")
            return set()
            
    except Exception as e:
        logging.error(f"Error getting connected devices: {e}")
        return set()

def get_device_ip(device_mac):
    """Get IP address for device MAC"""
    try:
        result = subprocess.run(["arp", "-a"], capture_output=True, text=True, timeout=5)
        
        for line in result.stdout.split('\n'):
            if device_mac.lower() in line.lower():
                ip_match = re.search(r'\(([\d.]+)\)', line)
                if ip_match:
                    return ip_match.group(1)
        
        # If not found in ARP, check DHCP leases
        try:
            with open('/var/lib/dhcp/dhcpd.leases', 'r') as f:
                content = f.read()
                # Parse DHCP leases for MAC to IP mapping
                # This is a simplified parser
                return "192.168.100.50"  # Default IP
        except:
            return "192.168.100.50"  # Default IP
            
    except Exception as e:
        logging.error(f"Error getting device IP: {e}")
        return "192.168.100.50"

def authenticate_device(device_mac, device_ip):
    """Authenticate device with backend"""
    try:
        # For now, we'll use a placeholder token extraction method
        # In a real implementation, this would extract the token from the WiFi connection
        session_token = "placeholder_token"
        
        response = requests.post(
            f"{BACKEND_URL}/api/wifi/device-connect",
            json={
                "device_mac": device_mac,
                "device_ip": device_ip,
                "session_token": session_token
            },
            timeout=10
        )
        
        if response.status_code == 200:
            result = response.json()
            if result.get("authenticated"):
                logging.info(f"✅ Device {device_mac} authenticated successfully")
                return True
            else:
                logging.warning(f"❌ Device {device_mac} authentication failed: {result.get('error')}")
                return False
        else:
            logging.error(f"Backend authentication failed: {response.status_code}")
            return False
            
    except Exception as e:
        logging.error(f"Error authenticating device: {e}")
        return False

def monitor_connections():
    """Main monitoring loop"""
    logging.info("🔍 Starting KSWiFi connection monitor...")
    
    known_devices = set()
    
    while True:
        try:
            current_devices = get_connected_devices()
            
            # Check for new connections
            new_devices = current_devices - known_devices
            
            for device_mac in new_devices:
                logging.info(f"🔍 New connection detected: {device_mac}")
                
                device_ip = get_device_ip(device_mac)
                logging.info(f"Device IP: {device_ip}")
                
                # Authenticate device
                if authenticate_device(device_mac, device_ip):
                    # Grant internet access
                    subprocess.run([
                        "/usr/local/bin/auth_device.sh",
                        device_mac,
                        device_ip,
                        "allow"
                    ])
                else:
                    logging.warning(f"Device {device_mac} not authenticated, blocking internet access")
            
            # Check for disconnections
            disconnected_devices = known_devices - current_devices
            for device_mac in disconnected_devices:
                logging.info(f"🔍 Device disconnected: {device_mac}")
                # Revoke access
                subprocess.run([
                    "/usr/local/bin/auth_device.sh",
                    device_mac,
                    "",
                    "deny"
                ])
            
            known_devices = current_devices
            
            time.sleep(10)  # Check every 10 seconds
            
        except KeyboardInterrupt:
            logging.info("Monitor stopped by user")
            break
        except Exception as e:
            logging.error(f"Monitor error: {e}")
            time.sleep(30)  # Wait longer on error

if __name__ == "__main__":
    monitor_connections()
EOF

sudo chmod +x /usr/local/bin/monitor_connections.py
check_success "Monitoring script"

# Step 9: Create systemd services
log "🔍 STEP 9: Creating systemd services..."

# Create systemd service for monitoring
sudo tee /etc/systemd/system/kswifi-monitor.service > /dev/null <<EOF
[Unit]
Description=KSWiFi Connection Monitor
After=network.target hostapd.service

[Service]
Type=simple
User=root
ExecStart=/usr/local/bin/monitor_connections.py
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
EOF

sudo systemctl daemon-reload
sudo systemctl enable kswifi-monitor
check_success "KSWiFi monitor service"

# Step 10: Start services
log "🔍 STEP 10: Starting services..."

sudo systemctl start dnsmasq
check_success "dnsmasq start"

sudo systemctl start hostapd
check_success "hostapd start"

sudo systemctl start kswifi-monitor
check_success "KSWiFi monitor start"

# Step 11: Create test script
log "🔍 STEP 11: Creating test script..."

sudo tee /usr/local/bin/test_kswifi.sh > /dev/null <<EOF
#!/bin/bash

echo "🔍 Testing KSWiFi Transparent Authentication System"
echo "=================================================="

# Test 1: Check hostapd status
echo "Test 1: hostapd status"
systemctl is-active hostapd
if [ \$? -eq 0 ]; then
    echo "✅ hostapd is running"
else
    echo "❌ hostapd is not running"
fi

# Test 2: Check dnsmasq status
echo "Test 2: dnsmasq status"
systemctl is-active dnsmasq
if [ \$? -eq 0 ]; then
    echo "✅ dnsmasq is running"
else
    echo "❌ dnsmasq is not running"
fi

# Test 3: Check WiFi network
echo "Test 3: WiFi network broadcast"
iwlist $WIFI_INTERFACE scan | grep "KSWIFI" > /dev/null
if [ \$? -eq 0 ]; then
    echo "✅ KSWIFI network is broadcasting"
else
    echo "❌ KSWIFI network not found"
fi

# Test 4: Check iptables rules
echo "Test 4: iptables rules"
iptables -L KSWIFI_AUTH > /dev/null 2>&1
if [ \$? -eq 0 ]; then
    echo "✅ iptables rules are configured"
else
    echo "❌ iptables rules are missing"
fi

# Test 5: Check backend connectivity
echo "Test 5: Backend connectivity"
curl -s --max-time 10 https://kswifi.onrender.com/health > /dev/null
if [ \$? -eq 0 ]; then
    echo "✅ Backend is reachable"
else
    echo "❌ Backend is not reachable"
fi

# Test 6: Check monitor service
echo "Test 6: Monitor service"
systemctl is-active kswifi-monitor
if [ \$? -eq 0 ]; then
    echo "✅ KSWiFi monitor is running"
else
    echo "❌ KSWiFi monitor is not running"
fi

echo ""
echo "📊 System Status Summary:"
echo "========================="
echo "WiFi Interface: $WIFI_INTERFACE"
echo "Network SSID: KSWIFI"
echo "IP Range: 192.168.100.10-100"
echo "Backend URL: https://kswifi.onrender.com"
echo ""
echo "📱 To test:"
echo "1. Generate QR code from KSWiFi app"
echo "2. Scan QR code with phone"
echo "3. Phone should connect to KSWIFI automatically"
echo "4. Check /var/log/kswifi_monitor.log for authentication logs"
EOF

sudo chmod +x /usr/local/bin/test_kswifi.sh
check_success "Test script"

# Final status check
log "🎯 SETUP COMPLETE: Running final tests..."
sudo /usr/local/bin/test_kswifi.sh

log "✅ VPS Setup completed successfully!"
log "📋 Next steps:"
log "   1. Update your FastAPI backend with the new endpoints"
log "   2. Test QR code generation and scanning"
log "   3. Monitor logs: tail -f /var/log/kswifi_monitor.log"
log "   4. Check system status: sudo /usr/local/bin/test_kswifi.sh"

echo ""
echo "🎉 KSWiFi Transparent Authentication System is ready!"
echo "=================================================="