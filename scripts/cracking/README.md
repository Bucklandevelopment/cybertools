# WiFi Cracking Module

This module contains scripts to automate the process of capturing and cracking WPA/WPA2 handshakes.

Todo: Include airgeddon plus hashcat and a rockyou :D

## `start_wpa_crack.sh`

This script provides a step-by-step guided workflow for cracking a WiFi network.

### How it Works

1.  **Monitor Mode**: It starts by putting your wireless card into monitor mode using `airmon-ng`.
2.  **Target Discovery**: It scans for available networks for a few seconds using `airodump-ng` so you can see the available targets.
3.  **User Input**: It prompts you to select the `BSSID` (the MAC address of the target AP) and the `Channel` it's operating on.
4.  **Handshake Capture**: It starts `airodump-ng` again, this time focused on the specific target, and waits to capture a WPA handshake. A handshake occurs when a device connects or reconnects to the network.
5.  **Deauthentication**: To speed up the process, the script automatically finds a connected client and sends deauthentication packets using `aireplay-ng`. This forces the client to disconnect and then immediately reconnect, generating a handshake for you to capture.
6.  **Cracking**: Once the handshake is captured, the script uses `aircrack-ng` and a specified wordlist to try and find the password.

### Usage

1.  **Install Dependencies**:
    ```bash
    sudo apt update
    sudo apt install -y aircrack-ng
    ```

2.  **Get a Wordlist**:
    The script is pre-configured to use `/usr/share/wordlists/rockyou.txt`. If you don't have this, you can install it or use your own:
    ```bash
    # Example of getting the rockyou wordlist
    sudo apt install -y wordlists
    sudo gzip -d /usr/share/wordlists/rockyou.txt.gz
    ```
    *Update the `WORDLIST_PATH` variable in the script if you use a different path.*

3.  **Run the Script**:
    ```bash
    sudo ./start_wpa_crack.sh
    ```
    Follow the on-screen prompts to select your target and run the attack.

---

### Disclaimer

**These scripts are for educational purposes and for use on networks you own or have explicit permission to test. Unauthorized wireless attacks are illegal.**
