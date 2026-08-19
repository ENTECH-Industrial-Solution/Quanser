@echo off
echo ==================================================
echo     QCar2 Map Reset (Virtual + Physical)
echo ==================================================
echo.

echo [1/4] หยุด QUARC models ที่กำลังรันอยู่...
quarc_run -q -Q *.rt-win64
timeout -t 2 /NOBREAK > nul

echo [2/4] Reset map และ Spawn วัตถุใหม่ (SetupEnvironment)...
python resources_qlab_setup/SetupEnvironment.py UseWeather
timeout -t 2 /NOBREAK > nul

echo [3/4] รัน Virtual Cars ใหม่...
quarc_run -D -r -t tcpip://localhost:17000 Simulink\QCar2_Virtual_Car1.rt-win64 -virtual_only 1
timeout -t 1 /NOBREAK > nul
quarc_run -D -r -t tcpip://localhost:17000 Simulink\QCar2_Virtual_Car2.rt-win64
timeout -t 1 /NOBREAK > nul
quarc_run -D -r -t tcpip://localhost:17000 Simulink\QCar2_Virtual_Car3.rt-win64
timeout -t 1 /NOBREAK > nul
quarc_run -D -r -t tcpip://localhost:17000 Simulink\Infrastructure_Server.rt-win64

echo [4/4] เริ่ม Traffic Controller ใหม่...
start "" python resources_qlab_setup/Traffic_Controller.py

echo.
echo ==================================================
echo ✓ Reset Map สำเร็จ! รถ QCar2 พร้อมวิ่งต่อแล้ว
echo ==================================================
echo.
pause
