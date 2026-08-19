@echo off
echo Start QCar2 DEMO
python spawn\spawn_qcar2.py
start "" python camera\view_virtual_qcar2_camera.py
python controller\run_virtual_qcar2_control.py
pause
