clear all;

% Various Timing Loops
CSI_Sample_Time = 1/60;
Controller_Sample_Time =CSI_Sample_Time/20;
RealSense_Sample_Time = CSI_Sample_Time*2;
NN_Sample_Time = RealSense_Sample_Time*1; %Used to be 3
% Joystick_Sample_Time = 16*Controller_Sample_Time;
% Audio_Sample_Time = 0.2;
ImageDisplay_Sample_Time = 120*Controller_Sample_Time;
% ImageDisplay_Sample_Time = NN_Sample_Time;
% LiDAR_Sample_Time = 0.25;
% LiDAR_Sample_Time = 0.1;
LiDAR_Sample_Time = CSI_Sample_Time*4;
LiDAR_Sample_Time = CSI_Sample_Time*3;

SPR = 384; %Scans per revolution for the LiDAR scan (Long Mode)
% SPR = 192; %Scans per revolution for the LiDAR scan (Short Mode)
Audio_Sample_Time = 0.3;
Initialization_Time = 5; %5 seconds to make sure all systems are good

cameraStepSize = 3e-2;
% cameraStepSize = 1e-2;


%Frames are 616x820
% ROWS = 616;
% COLUMNS = 820;
% 
% %ROI
% rows_length = 260;
% cols_length = 820;
% rows_start = ROWS-rows_length;
% rows = [rows_start:rows_start+rows_length];
% cols = [COLUMNS/2 - cols_length/2:COLUMNS/2 + cols_length/2];

% distance and angles need to be loaded from a file
% load distance_new;
% range = distance_new(2: length (distance_new), width (distance_new)-5);
% load angles_new;
% angles = angles_new(2: length (angles_new), width (angles_new)-5);
% range_indicies = find (range == 0);

% Old way of getting rid of 0 ranges
% for i = 1:length (range_indicies)
%     range (range_indicies(i)) =   range (range_indicies(i)-1);
% end
% 
% range(range_indicies) = [];
% angles(range_indicies) = [];

% load path data
% Create_Path_WS3_01;
% load Oakland_Car_Paths.mat;
% 
% loop_headings (1) = loop_headings (2);
% loop_headings (12) = (loop_headings (11) + loop_headings (13))/2;
% red_headings (1) = red_headings (2);
% green_headings (1) = green_headings (2);
% 
% load car sounds
load Car_Sounds.mat;

%% Gyro KF
GyroKF_sampleTime = 0.001;

GyroKF_X0 = [0;0];
GyroKF_P0 = eye(2);

GyroKF_Q = diag([0.01, 0.001]);
GyroKF_R = 0.01;


%% QCar EKF
QCarEKF_sampleTime = GyroKF_sampleTime;

QCarEKF_L = 0.24;

QcarKF_X0 = [0; 0; 0];
QCarEKF_P0 = eye(3);

QCarEKF_Q = diag([0.00001, 0.00001, 0.00001]);

QCarEKF_R_heading = diag(0.1);
QCarEKF_R_combined = diag([0.1, 0.1, 0.01]);

%% Loading the paths

load ("SDTS_Paths_6_2023.mat");
close all;
%figure
cal_pos = [-5.706, 2.55]/10 *0;

% hold on;
% plot (path_x4 - cal_pos(1), path_y4 - cal_pos(2));
% plot (path_x - cal_pos(1), path_y - cal_pos(2));
% plot (path_x3 - cal_pos(1), path_y3 - cal_pos(2));
% plot (path_x5 - cal_pos(1), path_y5 - cal_pos(2));
% plot (path_x6 - cal_pos(1), path_y6 - cal_pos(2));
% hold off;
