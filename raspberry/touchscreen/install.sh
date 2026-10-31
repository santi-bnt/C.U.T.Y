#!/bin/bash
set -euo pipefail
cuty_script_dir="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"
cd -- "$cuty_script_dir"
for file in cuty_launcher.py cuty_wifi_panel.py cuty-launcher.service; do
    [[ -f "$file" ]] || { echo "Falta $file"; exit 1; }
done
[[ -f /home/santi/cuty_touch_calibration.json ]] || { echo 'Falta la calibración validada'; exit 1; }
python3 -m py_compile cuty_launcher.py cuty_wifi_panel.py
systemd-analyze verify "$PWD/cuty-launcher.service"
if [[ -f /etc/systemd/system/cuty-launcher.service ]]; then
    sudo cp -a /etc/systemd/system/cuty-launcher.service "/etc/systemd/system/cuty-launcher.service.bak-$(date +%Y%m%d-%H%M%S)"
fi
sudo install -m 644 cuty-launcher.service /etc/systemd/system/cuty-launcher.service
sudo systemctl daemon-reload
sudo systemctl disable --now cuty-wifi-panel.service
sudo systemctl stop cuty-menu-test.service 2>/dev/null || true
sudo systemctl enable cuty-launcher.service
sudo systemctl restart cuty-launcher.service
sudo systemctl --no-pager --full status cuty-launcher.service
