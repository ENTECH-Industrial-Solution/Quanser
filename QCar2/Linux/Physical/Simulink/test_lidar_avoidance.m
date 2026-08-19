% Script สำหรับทดสอบฟังก์ชัน LiDAR_Obstacle_Detector และ LiDAR_Avoidance_FSM ใน MATLAB Command Window
clear; clc;

fprintf('=====================================================\n');
fprintf(' Testing LiDAR Obstacle Detector & Avoidance FSM \n');
fprintf('=====================================================\n\n');

% 1. จำลองข้อมูล LiDAR Scan 360 องศา (384 จุด)
num_points = 384;
Headings = linspace(-pi, pi, num_points);
Distances = 3.0 * ones(1, num_points);

% จำลองสิ่งกีดขวางระยะ 0.5m ที่ด้านหน้ามุม -10 ถึง +10 องศา
front_indices = find(abs(Headings) <= 10*pi/180);
Distances(front_indices) = 0.5;

fprintf('1. Testing LiDAR_Obstacle_Detector()...\n');
[min_front, min_left, min_right] = LiDAR_Obstacle_Detector(Distances, Headings);
fprintf('   - Min Front Distance: %.2f m\n', min_front);
fprintf('   - Min Left Distance:  %.2f m\n', min_left);
fprintf('   - Min Right Distance: %.2f m\n\n', min_right);

% 2. ทดสอบฟังก์ชัน LiDAR_Avoidance_FSM
fprintf('2. Testing LiDAR_Avoidance_FSM()...\n');
desired_speed = 0.25;
desired_steering = 0.0;
dt = 0.001; % 1ms sample time

[speed_cmd, steering_cmd] = LiDAR_Avoidance_FSM(desired_speed, desired_steering, min_front, min_left, min_right, dt);

fprintf('   - Output Speed Command:    %.2f m/s\n', speed_cmd);
fprintf('   - Output Steering Command: %.3f rad (%.1f deg)\n\n', steering_cmd, rad2deg(steering_cmd));

fprintf('SUCCESS! Both functions executed cleanly without errors.\n');
fprintf('-> ท่านสามารถนำโค้ดใน LiDAR_Obstacle_Detector.m และ LiDAR_Avoidance_FSM.m ไปวางทับใน MATLAB Function Block ใน Simulink ได้ทันที!\n');
