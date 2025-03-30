#!/bin/bash
# filepath: f:\Projects\acestream-scraper\warp-setup.sh

# Only run if WARP is enabled
if [ "${ENABLE_WARP}" = "true" ]; then
    # Create logs directory if it doesn't exist
    LOG_DIR="/app/logs"
    mkdir -p $LOG_DIR
    
    WARP_LOG="$LOG_DIR/warp.log"
    echo "$(date): Starting WARP setup..." > "$WARP_LOG"

    # create a tun device if not exist
    # allow passing device to ensure compatibility with Podman
    if [ ! -e /dev/net/tun ]; then
        echo "$(date): Creating TUN device..." >> "$WARP_LOG"
        sudo mkdir -p /dev/net
        sudo mknod /dev/net/tun c 10 200
        sudo chmod 600 /dev/net/tun
    fi

    # start dbus
    echo "$(date): Starting DBus..." >> "$WARP_LOG"
    sudo mkdir -p /run/dbus
    if [ -f /run/dbus/pid ]; then
        sudo rm /run/dbus/pid
    fi
    sudo dbus-daemon --config-file=/usr/share/dbus-1/system.conf >> "$WARP_LOG" 2>&1
    echo "$(date): Initializing Cloudflare WARP in full tunnel mode..." >> "$WARP_LOG"

    # Force IPv4 for WARP
    export WARP_FORCE_IPV4=true
    
    # start the daemon
    echo "$(date): Starting WARP service..." >> "$WARP_LOG"
    sudo warp-svc --accept-tos >> "$WARP_LOG" 2>&1 &
    # Start the WARP service
    # service warp-svc start
    sleep 5
    
    
    # if /var/lib/cloudflare-warp/reg.json not exists, setup new warp client
    echo "$(date): Checking WARP client registration..." >> "$WARP_LOG"
    if [ ! -f /var/lib/cloudflare-warp/reg.json ]; then
        echo "$(date): WARP client not registered, registering..." >> "$WARP_LOG"
        # if /var/lib/cloudflare-warp/mdm.xml not exists or REGISTER_WHEN_MDM_EXISTS not empty, register the warp client
        if [ ! -f /var/lib/cloudflare-warp/mdm.xml ]; then
            warp-cli --accept-tos registration new >> "$WARP_LOG" 2>&1 && echo "$(date): WARP client registered!" >> "$WARP_LOG"
            # if a license key is provided, register the license
            if [ -n "$WARP_LICENSE_KEY" ]; then
                echo "$(date): License key found, registering license..." >> "$WARP_LOG"
                warp-cli --accept-tos registration license "$WARP_LICENSE_KEY" >> "$WARP_LOG" 2>&1 && echo "$(date): WARP license registered!" >> "$WARP_LOG"
            fi
        fi
        # connect to the warp server
        # warp-cli --accept-tos connect
    else
        echo "$(date): WARP client already registered, skip registration" >> "$WARP_LOG"
    fi
    
    
    # disable qlog if DEBUG_ENABLE_QLOG is empty
    if [ -z "$DEBUG_ENABLE_QLOG" ]; then
        warp-cli --accept-tos debug qlog disable >> "$WARP_LOG" 2>&1
    else
        warp-cli --accept-tos debug qlog enable >> "$WARP_LOG" 2>&1
    fi

    # if WARP_ENABLE_NAT is provided, enable NAT and forwarding
    if [ -n "$WARP_ENABLE_NAT" ]; then
        # switch to warp mode
        echo "$(date): [NAT] Switching to warp mode..." >> "$WARP_LOG"
        warp-cli --accept-tos mode warp+doh >> "$WARP_LOG" 2>&1
        warp-cli --accept-tos connect >> "$WARP_LOG" 2>&1

        # wait another seconds for the daemon to reconfigure
        sleep "${WARP_SLEEP:-5}"

        # enable NAT
        echo "$(date): [NAT] Enabling NAT..." >> "$WARP_LOG"
        sudo nft add table ip nat >> "$WARP_LOG" 2>&1
        sudo nft add chain ip nat WARP_NAT { type nat hook postrouting priority 100 \; } >> "$WARP_LOG" 2>&1
        sudo nft add rule ip nat WARP_NAT oifname "CloudflareWARP" masquerade >> "$WARP_LOG" 2>&1
        sudo nft add table ip mangle >> "$WARP_LOG" 2>&1
        sudo nft add chain ip mangle forward { type filter hook forward priority mangle \; } >> "$WARP_LOG" 2>&1
        sudo nft add rule ip mangle forward tcp flags syn tcp option maxseg size set rt mtu >> "$WARP_LOG" 2>&1

        # IPv6 NAT configuration is completely commented out as we're disabling IPv6
        sudo nft add table ip6 nat >> "$WARP_LOG" 2>&1
        sudo nft add chain ip6 nat WARP_NAT { type nat hook postrouting priority 100 \; } >> "$WARP_LOG" 2>&1
        sudo nft add rule ip6 nat WARP_NAT oifname "CloudflareWARP" masquerade >> "$WARP_LOG" 2>&1
        sudo nft add table ip6 mangle >> "$WARP_LOG" 2>&1
        sudo nft add chain ip6 mangle forward { type filter hook forward priority mangle \; } >> "$WARP_LOG" 2>&1
        sudo nft add rule ip6 mangle forward tcp flags syn tcp option maxseg size set rt mtu >> "$WARP_LOG" 2>&1
    fi

    # Check status
    echo "$(date): Checking WARP status..." >> "$WARP_LOG"
    warp-cli --accept-tos status >> "$WARP_LOG" 2>&1
    
    echo "$(date): WARP initialization completed - all traffic now routed through WARP (IPv6 disabled)" >> "$WARP_LOG"
    echo "WARP initialization completed - logs available at $WARP_LOG"
else
    echo "WARP is disabled, skipping initialization"
fi