@echo off

echo =========================================================================
echo  Physical LiDAR Detection + Virtual QCar2 Demo Left Avoidance Controller
echo =========================================================================

echo Stopping all running QUARC models and clients...
quarc_run -q -Q *.rt-win64
quanser_host_peripheral_client.exe -q
quanser_host_peripheral_client.exe -q
quanser_host_peripheral_client.exe -q
timeout -t 3 /NOBREAK > nul

echo Setting up QLabs Cityscape Environment...
python resources_qlab_setup/SetupEnvironment.py UseWeather
timeout -t 3 /NOBREAK > nul

echo Starting QLabs Virtual Cars & Infrastructure Server...
quarc_run -D -r -t tcpip://localhost:17000 Simulink\QCar2_Virtual_Car1.rt-win64
quarc_run -D -r -t tcpip://localhost:17000 Simulink\QCar2_Virtual_Car2.rt-win64
quarc_run -D -r -t tcpip://localhost:17000 Simulink\QCar2_Virtual_Car3.rt-win64
quarc_run -D -r -t tcpip://localhost:17000 Simulink\Infrastructure_Server.rt-win64
timeout -t 2 /NOBREAK > nul

echo Launching Physical LiDAR Avoidance and Virtual QCar2 Controller...
python run_physical_lidar_avoidance.py

pause
