@echo off

echo =========================================================================
echo  Physical LiDAR Detection + Virtual QCar2 Lane Return Controller (Opt 1)
echo =========================================================================

echo Stopping any running QUARC models and clients to avoid command conflicts...
quarc_run -q -Q *.rt-win64
quanser_host_peripheral_client.exe -q
quanser_host_peripheral_client.exe -q
timeout -t 3 /NOBREAK > nul

echo Setting up QLabs Environment and Spawning Virtual Cars...
python resources_qlab_setup/SetupEnvironment.py UseWeather
timeout -t 3 /NOBREAK > nul

echo Launching Physical LiDAR Avoidance and Virtual QCar2 Controller...
python run_physical_lidar_avoidance.py

pause
