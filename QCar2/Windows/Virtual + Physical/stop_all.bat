@echo off

for /f "usebackq delims=" %%A in (`python -c "import json;print(json.load(open('network_config.json'))['qcar_ip'])"`) do set QCAR_IP=%%A

taskkill -f -im python*

quarc_run -q -Q *.rt-win64
quarc_run -q -Q -t tcpip://%QCAR_IP%:17000 *.rt-linux_qcar2

quanser_host_peripheral_client.exe -q
quanser_host_peripheral_client.exe -q
quanser_host_peripheral_client.exe -q

python ssh_qcar2 - stop.py
