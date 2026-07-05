#!/usr/bin/env bash
# Sentra end-to-end demo — starts the mock model + gateway, runs the customer app.
# No installs required (pure Python stdlib).
set -e
cd "$(dirname "$0")"

echo "==> starting mock upstream model (:8090)"
python3 demo/mock_upstream.py &
UP=$!
echo "==> starting Sentra gateway (:8100)"
python3 -m sentra.gateway &
GW=$!

# give servers a moment
python3 - <<'PY'
import time, urllib.request
for _ in range(30):
    try:
        urllib.request.urlopen("http://127.0.0.1:8100/events", timeout=1); break
    except Exception: time.sleep(0.2)
PY

echo "==> running customer app through Sentra"
python3 demo/customer_app.py

echo "==> demo done. (dashboard: http://127.0.0.1:8100/ )  Ctrl-C to stop servers."
trap "kill $UP $GW 2>/dev/null" EXIT
wait $GW
