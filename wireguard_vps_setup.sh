#!/bin/bash

# WireGuard VPN Server Setup for KSWiFi Connect System
# Run this script on Ubuntu 22.04 VPS

set -e  # Exit on any error

echo "🚀 Setting up KSWiFi Connect VPN Server"
echo "======================================="

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

# Step 1: Update system and install WireGuard
log "🔍 STEP 1: Installing WireGuard..."

sudo apt update && sudo apt upgrade -y
check_success "System update"

sudo apt install -y wireguard wireguard-tools qrencode curl jq python3-pip python3-venv
check_success "WireGuard installation"

# Step 2: Generate server keys
log "🔍 STEP 2: Generating server keys..."

cd /etc/wireguard
sudo wg genkey | sudo tee server_private.key | sudo wg pubkey | sudo tee server_public.key
sudo chmod 600 server_private.key
check_success "Server key generation"

SERVER_PRIVATE_KEY=$(sudo cat server_private.key)
SERVER_PUBLIC_KEY=$(sudo cat server_public.key)

log "ℹ️  Server public key: $SERVER_PUBLIC_KEY"

# Step 3: Get server public IP
log "🔍 STEP 3: Getting server public IP..."

SERVER_PUBLIC_IP=$(curl -s ifconfig.me)
if [ -z "$SERVER_PUBLIC_IP" ]; then
    log "❌ Could not determine public IP"
    exit 1
fi

log "ℹ️  Server public IP: $SERVER_PUBLIC_IP"

# Step 4: Create WireGuard server configuration
log "🔍 STEP 4: Creating WireGuard server configuration..."

sudo tee /etc/wireguard/wg0.conf > /dev/null <<EOF
[Interface]
PrivateKey = $SERVER_PRIVATE_KEY
Address = 10.8.0.1/24
ListenPort = 51820
SaveConfig = true

# Enable IP forwarding and NAT
PostUp = echo 1 > /proc/sys/net/ipv4/ip_forward
PostUp = iptables -A FORWARD -i %i -j ACCEPT; iptables -A FORWARD -o %i -j ACCEPT; iptables -t nat -A POSTROUTING -o eth0 -j MASQUERADE
PostDown = iptables -D FORWARD -i %i -j ACCEPT; iptables -D FORWARD -o %i -j ACCEPT; iptables -t nat -D POSTROUTING -o eth0 -j MASQUERADE

# Clients will be added dynamically by backend
EOF

sudo chmod 600 /etc/wireguard/wg0.conf
check_success "WireGuard server configuration"

# Step 5: Enable IP forwarding
log "🔍 STEP 5: Enabling IP forwarding..."

echo 'net.ipv4.ip_forward=1' | sudo tee -a /etc/sysctl.conf
sudo sysctl -p
check_success "IP forwarding"

# Step 6: Configure firewall
log "🔍 STEP 6: Configuring firewall..."

# Allow WireGuard port
sudo ufw allow 51820/udp

# Allow SSH (important!)
sudo ufw allow ssh

# Enable firewall
sudo ufw --force enable
check_success "Firewall configuration"

# Step 7: Start WireGuard service
log "🔍 STEP 7: Starting WireGuard service..."

sudo systemctl enable wg-quick@wg0
sudo systemctl start wg-quick@wg0
check_success "WireGuard service start"

# Step 8: Create client management scripts
log "🔍 STEP 8: Creating client management scripts..."

# Script to add new client
sudo tee /usr/local/bin/add_kswifi_client.sh > /dev/null <<'EOF'
#!/bin/bash

CLIENT_NAME=$1
CLIENT_IP=$2

if [ -z "$CLIENT_NAME" ] || [ -z "$CLIENT_IP" ]; then
    echo "Usage: $0 <client_name> <client_ip>"
    exit 1
fi

cd /etc/wireguard

# Generate client keys
CLIENT_PRIVATE_KEY=$(wg genkey)
CLIENT_PUBLIC_KEY=$(echo $CLIENT_PRIVATE_KEY | wg pubkey)

# Add client to server config
echo "" >> wg0.conf
echo "# Client: $CLIENT_NAME" >> wg0.conf
echo "[Peer]" >> wg0.conf
echo "PublicKey = $CLIENT_PUBLIC_KEY" >> wg0.conf
echo "AllowedIPs = $CLIENT_IP/32" >> wg0.conf

# Reload WireGuard
wg syncconf wg0 <(wg-quick strip wg0)

# Output client configuration
echo "Client configuration for $CLIENT_NAME:"
echo "======================================"
cat <<EOL
[Interface]
PrivateKey = $CLIENT_PRIVATE_KEY
Address = $CLIENT_IP/24
DNS = 8.8.8.8, 8.8.4.4

[Peer]
PublicKey = $(cat server_public.key)
Endpoint = $(curl -s ifconfig.me):51820
AllowedIPs = 0.0.0.0/0
PersistentKeepalive = 25
EOL
EOF

sudo chmod +x /usr/local/bin/add_kswifi_client.sh
check_success "Client management script"

# Script to remove client
sudo tee /usr/local/bin/remove_kswifi_client.sh > /dev/null <<'EOF'
#!/bin/bash

CLIENT_PUBLIC_KEY=$1

if [ -z "$CLIENT_PUBLIC_KEY" ]; then
    echo "Usage: $0 <client_public_key>"
    exit 1
fi

# Remove client from WireGuard
wg set wg0 peer $CLIENT_PUBLIC_KEY remove

echo "Client removed: $CLIENT_PUBLIC_KEY"
EOF

sudo chmod +x /usr/local/bin/remove_kswifi_client.sh
check_success "Client removal script"

# Step 9: Create API integration script
log "🔍 STEP 9: Creating API integration script..."

sudo tee /usr/local/bin/kswifi_api.py > /dev/null <<'EOF'
#!/usr/bin/env python3

import subprocess
import json
import sys
import secrets
import base64
from datetime import datetime

def generate_client_config(session_id, data_limit_mb, client_name):
    """Generate WireGuard client configuration"""
    
    # Get next available IP
    result = subprocess.run(['wg', 'show', 'wg0', 'allowed-ips'], capture_output=True, text=True)
    used_ips = []
    for line in result.stdout.split('\n'):
        if '10.8.0.' in line:
            ip = line.split('/')[0].strip()
            if ip.startswith('10.8.0.'):
                used_ips.append(int(ip.split('.')[-1]))
    
    # Find next available IP (start from 10.8.0.2)
    client_ip_num = 2
    while client_ip_num in used_ips:
        client_ip_num += 1
    
    client_ip = f"10.8.0.{client_ip_num}"
    
    # Generate client keys
    private_key = subprocess.run(['wg', 'genkey'], capture_output=True, text=True).stdout.strip()
    public_key = subprocess.run(['wg', 'pubkey'], input=private_key, text=True, capture_output=True).stdout.strip()
    
    # Get server public key
    with open('/etc/wireguard/server_public.key', 'r') as f:
        server_public_key = f.read().strip()
    
    # Get server public IP
    server_ip = subprocess.run(['curl', '-s', 'ifconfig.me'], capture_output=True, text=True).stdout.strip()
    
    # Add client to server
    peer_config = f"""
# Client: {client_name} (Session: {session_id})
[Peer]
PublicKey = {public_key}
AllowedIPs = {client_ip}/32
"""
    
    with open('/etc/wireguard/wg0.conf', 'a') as f:
        f.write(peer_config)
    
    # Reload WireGuard
    subprocess.run(['wg', 'syncconf', 'wg0', '/dev/stdin'], input=subprocess.run(['wg-quick', 'strip', 'wg0'], capture_output=True, text=True).stdout, text=True)
    
    # Generate client configuration
    client_config = f"""[Interface]
PrivateKey = {private_key}
Address = {client_ip}/24
DNS = 8.8.8.8, 8.8.4.4

[Peer]
PublicKey = {server_public_key}
Endpoint = {server_ip}:51820
AllowedIPs = 0.0.0.0/0
PersistentKeepalive = 25

# KSWiFi Connect Session
# Session ID: {session_id}
# Data Limit: {data_limit_mb}MB
# Created: {datetime.now().isoformat()}
"""
    
    return {
        "client_config": client_config,
        "client_ip": client_ip,
        "public_key": public_key,
        "private_key": private_key
    }

def remove_client(public_key):
    """Remove client from WireGuard"""
    subprocess.run(['wg', 'set', 'wg0', 'peer', public_key, 'remove'])
    return {"removed": True, "public_key": public_key}

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python3 kswifi_api.py <command> [args...]")
        sys.exit(1)
    
    command = sys.argv[1]
    
    if command == "add_client":
        session_id = sys.argv[2]
        data_limit_mb = int(sys.argv[3])
        client_name = sys.argv[4]
        
        result = generate_client_config(session_id, data_limit_mb, client_name)
        print(json.dumps(result))
        
    elif command == "remove_client":
        public_key = sys.argv[2]
        result = remove_client(public_key)
        print(json.dumps(result))
        
    else:
        print(f"Unknown command: {command}")
        sys.exit(1)
EOF

sudo chmod +x /usr/local/bin/kswifi_api.py
check_success "API integration script"

# Step 10: Create monitoring script
log "🔍 STEP 10: Creating monitoring script..."

sudo tee /usr/local/bin/monitor_kswifi.py > /dev/null <<'EOF'
#!/usr/bin/env python3

import subprocess
import time
import json
import requests
import logging
from datetime import datetime

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='[%(asctime)s] %(levelname)s: %(message)s',
    handlers=[
        logging.FileHandler('/var/log/kswifi_vpn.log'),
        logging.StreamHandler()
    ]
)

BACKEND_URL = "https://kswifi.onrender.com"

def get_connected_clients():
    """Get list of connected VPN clients"""
    try:
        result = subprocess.run(['wg', 'show', 'wg0', 'dump'], capture_output=True, text=True)
        
        clients = []
        for line in result.stdout.split('\n')[1:]:  # Skip header
            if line.strip():
                parts = line.split('\t')
                if len(parts) >= 6:
                    clients.append({
                        'public_key': parts[0],
                        'endpoint': parts[2] if parts[2] != '(none)' else None,
                        'allowed_ips': parts[3],
                        'latest_handshake': parts[4],
                        'transfer_rx': int(parts[5]) if parts[5] != '0' else 0,
                        'transfer_tx': int(parts[6]) if parts[6] != '0' else 0
                    })
        
        return clients
        
    except Exception as e:
        logging.error(f"Error getting connected clients: {e}")
        return []

def monitor_sessions():
    """Monitor VPN sessions and enforce limits"""
    logging.info("🔍 Starting KSWiFi Connect VPN monitor...")
    
    while True:
        try:
            clients = get_connected_clients()
            logging.info(f"📊 Active connections: {len(clients)}")
            
            for client in clients:
                # Calculate data usage (RX + TX)
                total_bytes = client['transfer_rx'] + client['transfer_tx']
                total_mb = total_bytes / (1024 * 1024)
                
                logging.info(f"📱 Client {client['public_key'][:8]}... used {total_mb:.2f}MB")
                
                # Report usage to backend (for session limit enforcement)
                try:
                    response = requests.post(
                        f"{BACKEND_URL}/api/connect/update-usage",
                        json={
                            "client_public_key": client['public_key'],
                            "data_used_mb": total_mb,
                            "last_seen": datetime.now().isoformat()
                        },
                        timeout=10
                    )
                    
                    if response.status_code == 200:
                        result = response.json()
                        if not result.get("session_valid", True):
                            # Session expired or limit exceeded - disconnect client
                            logging.info(f"🚫 Disconnecting client {client['public_key'][:8]}... (session expired)")
                            subprocess.run(['wg', 'set', 'wg0', 'peer', client['public_key'], 'remove'])
                            
                except Exception as e:
                    logging.error(f"Error reporting usage for client {client['public_key'][:8]}...: {e}")
            
            time.sleep(30)  # Check every 30 seconds
            
        except KeyboardInterrupt:
            logging.info("Monitor stopped by user")
            break
        except Exception as e:
            logging.error(f"Monitor error: {e}")
            time.sleep(60)

if __name__ == "__main__":
    monitor_sessions()
EOF

sudo chmod +x /usr/local/bin/monitor_kswifi.py
check_success "VPN monitoring script"

# Step 11: Create systemd service for monitoring
log "🔍 STEP 11: Creating systemd service..."

sudo tee /etc/systemd/system/kswifi-vpn-monitor.service > /dev/null <<EOF
[Unit]
Description=KSWiFi Connect VPN Monitor
After=network.target wg-quick@wg0.service

[Service]
Type=simple
User=root
ExecStart=/usr/local/bin/monitor_kswifi.py
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
EOF

sudo systemctl daemon-reload
sudo systemctl enable kswifi-vpn-monitor
sudo systemctl start kswifi-vpn-monitor
check_success "VPN monitor service"

# Step 12: Create test script
log "🔍 STEP 12: Creating test script..."

sudo tee /usr/local/bin/test_kswifi_vpn.sh > /dev/null <<EOF
#!/bin/bash

echo "🔍 Testing KSWiFi Connect VPN Server"
echo "===================================="

# Test 1: Check WireGuard status
echo "Test 1: WireGuard status"
systemctl is-active wg-quick@wg0
if [ \$? -eq 0 ]; then
    echo "✅ WireGuard is running"
else
    echo "❌ WireGuard is not running"
fi

# Test 2: Check interface
echo "Test 2: WireGuard interface"
ip addr show wg0 > /dev/null 2>&1
if [ \$? -eq 0 ]; then
    echo "✅ wg0 interface exists"
    ip addr show wg0 | grep "inet 10.8.0.1"
else
    echo "❌ wg0 interface missing"
fi

# Test 3: Check listening port
echo "Test 3: WireGuard port"
ss -ulnp | grep ":51820" > /dev/null
if [ \$? -eq 0 ]; then
    echo "✅ WireGuard listening on port 51820"
else
    echo "❌ WireGuard not listening on port 51820"
fi

# Test 4: Check connected clients
echo "Test 4: Connected clients"
CLIENT_COUNT=\$(wg show wg0 peers | wc -l)
echo "📱 Connected clients: \$CLIENT_COUNT"

# Test 5: Check monitor service
echo "Test 5: Monitor service"
systemctl is-active kswifi-vpn-monitor
if [ \$? -eq 0 ]; then
    echo "✅ KSWiFi monitor is running"
else
    echo "❌ KSWiFi monitor is not running"
fi

# Test 6: Check backend connectivity
echo "Test 6: Backend connectivity"
curl -s --max-time 10 https://kswifi.onrender.com/health > /dev/null
if [ \$? -eq 0 ]; then
    echo "✅ Backend is reachable"
else
    echo "❌ Backend is not reachable"
fi

echo ""
echo "📊 VPN Server Status:"
echo "===================="
echo "Server IP: \$(curl -s ifconfig.me)"
echo "VPN Network: 10.8.0.1/24"
echo "Listen Port: 51820"
echo "Backend: https://kswifi.onrender.com"
echo ""
echo "📋 Server Configuration:"
cat /etc/wireguard/wg0.conf
echo ""
echo "📱 To add test client:"
echo "sudo /usr/local/bin/add_kswifi_client.sh test_user 10.8.0.100"
EOF

sudo chmod +x /usr/local/bin/test_kswifi_vpn.sh
check_success "VPN test script"

# Step 13: Save server information for backend integration
log "🔍 STEP 13: Saving server information..."

sudo tee /etc/wireguard/server_info.json > /dev/null <<EOF
{
    "server_public_key": "$SERVER_PUBLIC_KEY",
    "server_public_ip": "$SERVER_PUBLIC_IP",
    "server_port": 51820,
    "vpn_network": "10.8.0.0/24",
    "dns_servers": ["8.8.8.8", "8.8.4.4"],
    "setup_date": "$(date -Iseconds)"
}
EOF

check_success "Server information save"

# Final test
log "🎯 SETUP COMPLETE: Running final tests..."
sudo /usr/local/bin/test_kswifi_vpn.sh

log "✅ KSWiFi Connect VPN Server setup completed!"
log "📋 Next steps:"
log "   1. Update FastAPI backend with VPN integration"
log "   2. Test client configuration generation"
log "   3. Monitor logs: tail -f /var/log/kswifi_vpn.log"
log "   4. Check system status: sudo /usr/local/bin/test_kswifi_vpn.sh"

echo ""
echo "📄 Server Information (for backend integration):"
cat /etc/wireguard/server_info.json

echo ""
echo "🎉 KSWiFi Connect VPN Server is ready!"
echo "===================================="
EOF