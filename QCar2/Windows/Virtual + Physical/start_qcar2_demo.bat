@echo off

echo Stopping all running models and clients...
quarc_run -q -Q *.rt-win64
quanser_host_peripheral_client.exe -q
quanser_host_peripheral_client.exe -q
quanser_host_peripheral_client.exe -q
timeout -t 3 /NOBREAK > nul

echo Starting physical controller...
cd "C:\Users\Jirapat Chumaungphan\Documents\Quanser\QCar2\Windows\Virtual + Physical\Simulink"
start QCar2_Physical.slx

timeout -t 5 /NOBREAK > nul

set /p CONT=Please connect to the QCar model and press any key to continue...: 

echo Starting peripheral client...
start "" quanser_host_peripheral_client.exe -uri tcpip://localhost:18001
start "" quanser_host_peripheral_client.exe -uri tcpip://localhost:18002
start "" quanser_host_peripheral_client.exe -uri tcpip://localhost:18003

cd ..

echo starting Yolo model
start "" python ssh_qcar2.py

echo Starting 360 Vision
start "" python view_physical_360_vision.py

echo setting up Cityscape
python resources_qlab_setup/SetupEnvironment.py UseWeather

echo Running the cars
quarc_run -D -r -t tcpip://localhost:17000 Simulink\QCar2_Virtual_Car1.rt-win64 -virtual_only 0 -physical_uri tcpip://192.168.2.11:777
timeout -t 1 /NOBREAK > nul
quarc_run -D -r -t tcpip://localhost:17000 Simulink\QCar2_Virtual_Car2.rt-win64
timeout -t 1 /NOBREAK > nul
quarc_run -D -r -t tcpip://localhost:17000 Simulink\QCar2_Virtual_Car3.rt-win64
timeout -t 1 /NOBREAK > nul
quarc_run -D -r -t tcpip://localhost:17000 Simulink\Infrastructure_Server.rt-win64
timeout -t 1 /NOBREAK > nul

echo Starting the Traffic Controller
python resources_qlab_setup/Traffic_Controller.py -ip 192.168.2.11