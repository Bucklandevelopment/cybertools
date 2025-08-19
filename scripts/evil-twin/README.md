# Evil Twin AP Module

This module contains scripts to create an Evil Twin Access Point.

## `start_evil_twin.sh`

This is the main script to launch the attack.

### How it Works

1.  **Configuration**: The script is configured with two wireless interfaces: one for connecting to the internet (`INTERNET_IF`) and one for broadcasting the fake AP (`AP_IF`).
2.  **AP Interface Setup**: It assigns a static IP address to the `AP_IF`.
3.  **IP Forwarding & NAT**: It configures the Linux kernel to forward traffic from the `AP_IF` to the `INTERNET_IF`, effectively turning the Raspberry Pi into a router.
4.  **DHCP/DNS**: It starts `dnsmasq` to assign IP addresses and handle DNS requests for clients who connect to the fake AP.
5.  **Fake AP**: It starts `hostapd` to broadcast a wireless network with a specified ESSID and channel.
6.  **Deauthentication (Optional)**: If a target BSSID is provided, it launches an `aireplay-ng` deauthentication attack to disconnect clients from their legitimate network, encouraging them to connect to the fake one.

### Usage

1.  **Install Dependencies**:
    ```bash
    sudo apt update
    sudo apt install -y hostapd dnsmasq aircrack-ng
    ```

2.  **Configure the Script**:
    Edit `start_evil_twin.sh` and set the following variables:
    *   `INTERNET_IF`: Your internet-connected interface (e.g., `wlan0`).
    *   `AP_IF`: Your external WiFi card for the fake AP (e.g., `wlan1`).
    *   `AP_ESSID`: The name of the fake network you want to create.
    *   `TARGET_BSSID` (Optional): The MAC address of the real AP you want to impersonate.

3.  **Run the Script**:
    ```bash
    sudo ./start_evil_twin.sh
    ```

### Traffic Analysis

Once clients are connected, you can use tools like `tshark` (the command-line version of Wireshark) to capture and analyze their traffic on the `AP_IF` interface:

```bash
# Capture all traffic on the AP interface
sudo tshark -i <AP_IF> -w evil_twin_capture.pcap

# Capture specific traffic, like HTTP GET requests
sudo tshark -i <AP_IF> -Y "http.request.method == GET"
```
