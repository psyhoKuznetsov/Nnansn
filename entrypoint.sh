#!/bin/bash
set -e

keep_alive_local() {
    sleep 30
    if [ -z "$RENDER_EXTERNAL_HOSTNAME" ]; then
        exit 1
    fi
    while true; do
        curl -s "https://$RENDER_EXTERNAL_HOSTNAME" -o /dev/null &
        sleep 30
    done
}
keep_alive_local &

exec python bot.py
