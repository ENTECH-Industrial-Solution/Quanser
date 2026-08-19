@echo off

echo Stopping all running models and clients...
quarc_run -q -Q *.rt-win64
quanser_host_peripheral_client.exe -q
quanser_host_peripheral_client.exe -q
quanser_host_peripheral_client.exe -q
timeout -t 5 /NOBREAK > nul

echo Starting peripheral client...
start quanser_host_peripheral_client.exe -uri tcpip://localhost:18001
start quanser_host_peripheral_client.exe -uri tcpip://localhost:18002
start quanser_host_peripheral_client.exe -uri tcpip://localhost:18003
timeout -t 5 /NOBREAK > nul

echo setting up Cityscape
python resources_qlab_setup/SetupEnvironment.py UseWeather

echo Running the virtual cars
quarc_run -D -r -t tcpip://localhost:17000 Simulink\QCar2_Virtual_Car1.rt-win64 -virtual_only 1
timeout -t 1 /NOBREAK > nul
quarc_run -D -r -t tcpip://localhost:17000 Simulink\QCar2_Virtual_Car2.rt-win64
timeout -t 1 /NOBREAK > nul
quarc_run -D -r -t tcpip://localhost:17000 Simulink\QCar2_Virtual_Car3.rt-win64
timeout -t 1 /NOBREAK > nul
quarc_run -D -r -t tcpip://localhost:17000 Simulink\Infrastructure_Server.rt-win64

echo Starting the Traffic Controller
start "" python resources_qlab_setup/Traffic_Controller.py

echo Starting Virtual Camera
start "" python view_virtual_cameras.py
