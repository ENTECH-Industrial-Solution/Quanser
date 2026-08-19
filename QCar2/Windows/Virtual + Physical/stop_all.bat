@echo off

taskkill -f -im python*

quarc_run -q -Q *.rt-win64
quarc_run -q -Q -t tcpip://192.168.2.11:17000 *.rt-linux_qcar2

quanser_host_peripheral_client.exe -q
quanser_host_peripheral_client.exe -q
quanser_host_peripheral_client.exe -q

python ssh_qcar2 - stop.py
