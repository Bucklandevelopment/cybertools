#!/bin/bash

# ====================================================================================
# Dependency Installer for SCANet Wireless Toolkit
#
# Installs all necessary packages for the capture, cracking, and evil twin modules.
# ====================================================================================

echo "[*] Updating package lists..."
sudo apt update

echo "[*] Installing core dependencies..."
sudo apt install -y dkms build-essential bc libelf-dev linux-headers-$(uname -r) git

echo "[*] Installing wireless tools (aircrack-ng suite)..."
sudo apt install -y aircrack-ng

echo "[*] Installing tools for Evil Twin module..."
sudo apt install -y hostapd dnsmasq

echo "[*] Installing optional but recommended tools..."
sudo apt install -y wireshark kismet bettercap wifite

echo "[*] Installing hashcat for faster WPA cracking..."
sudo apt install -y hashcat hcxtools

echo "[*] Installing airgeddon (automated wireless auditing tool)..."
if [ ! -d "/opt/airgeddon" ]; then
    sudo git clone https://github.com/v1s1t0r1sh3r3/airgeddon.git /opt/airgeddon
    sudo chmod +x /opt/airgeddon/airgeddon.sh
    echo "[+] Airgeddon installed to /opt/airgeddon/"
else
    echo "[+] Airgeddon already installed"
fi

echo "[*] Installing Realtek RTL8814AU driver..."
# This driver is common for the Alfa AWUS1900
sudo apt install -y realtek-rtl8814au-dkms

echo "[+] All dependencies installed successfully."
echo "[*] You may need to reboot for all changes to take effect."
