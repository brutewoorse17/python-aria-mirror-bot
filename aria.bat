IF "%BT_STOP_TIMEOUT%"=="" set BT_STOP_TIMEOUT=600
aria2c --enable-rpc --rpc-listen-all=false --rpc-listen-port 6800  --max-connection-per-server=10 --rpc-max-request-size=1024M --seed-time=0.01 --min-split-size=10M --follow-torrent=mem --split=10 --bt-stop-timeout=%BT_STOP_TIMEOUT% --daemon=true --allow-overwrite=true
