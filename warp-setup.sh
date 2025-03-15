#!/bin/bash
# filepath: f:\Projects\acestream-scraper\warp-setup.sh

# Only run if WARP is enabled
if [ "${ENABLE_WARP}" = "true" ]; then
    # create a tun device if not exist
    # allow passing device to ensure compatibility with Podman
    if [ ! -e /dev/net/tun ]; then
        sudo mkdir -p /dev/net
        sudo mknod /dev/net/tun c 10 200
        sudo chmod 600 /dev/net/tun
    fi

    # start dbus
    sudo mkdir -p /run/dbus
    if [ -f /run/dbus/pid ]; then
        sudo rm /run/dbus/pid
    fi
    sudo dbus-daemon --config-file=/usr/share/dbus-1/system.conf
    echo "Initializing Cloudflare WARP in full tunnel mode..."
    # start the daemon
    sudo warp-svc --accept-tos &
    # Start the WARP service
    # service warp-svc start
    sleep 5
    
    # if /var/lib/cloudflare-warp/reg.json not exists, setup new warp client
    echo "checking warp client registration..."
    if [ ! -f /var/lib/cloudflare-warp/reg.json ]; then
        echo "Warp client not registered, registering..."
        # if /var/lib/cloudflare-warp/mdm.xml not exists or REGISTER_WHEN_MDM_EXISTS not empty, register the warp client
        if [ ! -f /var/lib/cloudflare-warp/mdm.xml ]; then
            warp-cli --accept-tos registration new && echo "Warp client registered!"
            # if a license key is provided, register the license
            if [ -n "$WARP_LICENSE_KEY" ]; then
                echo "License key found, registering license..."
                warp-cli --accept-tos registration license "$WARP_LICENSE_KEY" && echo "Warp license registered!"
            fi
        fi
        # connect to the warp server
        warp-cli --accept-tos connect
    else
        echo "Warp client already registered, skip registration"
    fi
    # disable qlog if DEBUG_ENABLE_QLOG is empty
    if [ -z "$DEBUG_ENABLE_QLOG" ]; then
        warp-cli --accept-tos debug qlog disable
    else
        warp-cli --accept-tos debug qlog enable
    fi

    # if WARP_ENABLE_NAT is provided, enable NAT and forwarding
    if [ -n "$WARP_ENABLE_NAT" ]; then
        # switch to warp mode
        echo "[NAT] Switching to warp mode..."
        warp-cli --accept-tos mode warp
        warp-cli --accept-tos connect

        # wait another seconds for the daemon to reconfigure
        sleep "$WARP_SLEEP"

        # enable NAT
        echo "[NAT] Enabling NAT..."
        sudo nft add table ip nat
        sudo nft add chain ip nat WARP_NAT { type nat hook postrouting priority 100 \; }
        sudo nft add rule ip nat WARP_NAT oifname "CloudflareWARP" masquerade
        sudo nft add table ip mangle
        sudo nft add chain ip mangle forward { type filter hook forward priority mangle \; }
        sudo nft add rule ip mangle forward tcp flags syn tcp option maxseg size set rt mtu

        sudo nft add table ip6 nat
        sudo nft add chain ip6 nat WARP_NAT { type nat hook postrouting priority 100 \; }
        sudo nft add rule ip6 nat WARP_NAT oifname "CloudflareWARP" masquerade
        sudo nft add table ip6 mangle
        sudo nft add chain ip6 mangle forward { type filter hook forward priority mangle \; }
        sudo nft add rule ip6 mangle forward tcp flags syn tcp option maxseg size set rt mtu
    fi

    
    # Check status
    warp-cli --accept-tos status
    
    echo "WARP initialization completed - all traffic now routed through WARP"
else
    echo "WARP is disabled, skipping initialization"
fi