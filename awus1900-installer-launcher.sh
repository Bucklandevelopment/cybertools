#!/bin/bash

# enhance with system parameters on the commented script
sudo apt update 
# && sudo apt full-upgrade -y maybe later :P
sudo apt install -y dkms build-essential bc libelf-dev linux-headers-$(uname -r) git
sudo apt install aircrack-ng wireshark kismet bettercap wifite
git clone https://github.com/aircrack-ng/rtl8814au.git
cd rtl8814au
sudo make dkms_install
sudo modprobe 8814au
iwconfig
sudo airmon-ng start wlan1
# sudo aireplay-ng --test wlan1 maybe later xD

sudo airodump-ng wlan1 --write scanet --output-format csv


# todo: 
: '
```bash
#!/bin/bash

# ---------- CONFIGURACIÓN ----------

OUTPUT_DIR="/home/kali/airodump_logs"
LOG_FILE="$OUTPUT_DIR/audit.log"
MAX_WAIT_TIME=120  # Tiempo máximo de espera por wlan1
SLEEP_INTERVAL=5
INTERFACE="wlan1"

mkdir -p "$OUTPUT_DIR"

log() {
    echo "[$(date +'%Y-%m-%d %H:%M:%S')] $*" | tee -a "$LOG_FILE"
}

log "=== Auditoría WiFi iniciada ==="

# ---------- ESPERA A QUE wlan1 ESTÉ DISPONIBLE ----------

TIME_ELAPSED=0
while ! ip link show $INTERFACE > /dev/null 2>&1; do
    sleep $SLEEP_INTERVAL
    TIME_ELAPSED=$((TIME_ELAPSED + SLEEP_INTERVAL))
    if [ $TIME_ELAPSED -ge $MAX_WAIT_TIME ]; then
        log "ERROR: $INTERFACE no apareció tras $MAX_WAIT_TIME segundos. Cancelando."
        exit 1
    fi
done

log "Interfaz $INTERFACE detectada."

# ---------- VERIFICA RTL8814AU ----------

if ! lsusb | grep -i 'RTL8814AU' >/dev/null; then
    log "ERROR: Dispositivo RTL8814AU no detectado. Cancelando."
    exit 1
fi

log "Dispositivo RTL8814AU presente."

# ---------- PONER EN MODO MONITOR (SOLO SI HACE FALTA) ----------

log "Verificando modo monitor para $INTERFACE..."

# Forzar apagado de NetworkManager si interfiere

sudo airmon-ng check kill >> "$LOG_FILE" 2>&1

# Intentar modo monitor en la misma interfaz

sudo ip link set $INTERFACE down
sudo iw dev $INTERFACE set type monitor
sudo ip link set $INTERFACE up

sleep 2

# Confirmar que quedó en modo monitor

MODE=$(iwconfig $INTERFACE 2>/dev/null | grep -i "mode" | awk '{print $4}')
if [[ "$MODE" != *Monitor* ]]; then
    log "ERROR: No se pudo activar el modo monitor en $INTERFACE."
    exit 1
fi

log "$INTERFACE está en modo monitor. Iniciando escaneo..."

# ---------- GENERA NOMBRE DE ARCHIVO ----------

NOW=$(date +'%Y-%m-%dT%H%M%S')
ID=$(openssl rand -hex 3)
FILENAME="${OUTPUT_DIR}/${NOW}_${ID}"

log "Comando lanzado: airodump-ng $INTERFACE --write $FILENAME --output-format csv"

# ---------- LANZA AIRODUMP SIN LÍMITE DE TIEMPO ----------

sudo airodump-ng "$INTERFACE" --write "$FILENAME" --output-format csv >> "$LOG_FILE" 2>&1

log "airodump-ng finalizó."
```
'


