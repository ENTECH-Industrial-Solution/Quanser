function [speed_cmd, steering_cmd] = LiDAR_Avoidance_FSM(desired_speed, desired_steering, min_front, min_left, min_right, dt)
    % persistent variables สำหรับจำสถานะ FSM ใน Simulink
    persistent fsm_state state_timer avoid_dir
    if isempty(fsm_state)
        fsm_state = 0;   % 0: NORMAL DEMO, 1: AVOID_LEFT, 2: PASS, 3: RETURN
        state_timer = 0;
        avoid_dir = 1;   % 1: Left, -1: Right
    end
    
    % ค่าเริ่มต้นสำหรับ MATLAB Coder (ป้องกัน undefined execution paths)
    speed_cmd = desired_speed;
    steering_cmd = desired_steering;
    
    steer_angle = 0.42; % มุมพวงมาลัยหักหลบ (rad) (~24 องศา)
    avoid_time  = 1.5;  % เวลาหักออกซ้าย (วินาที)
    pass_time   = 2.0;  % เวลาขับแซงขนาน (วินาที)
    return_time = 1.4;  % เวลาหักกลับเข้าเลน (วินาที)
    
    switch fsm_state
        case 0 % NORMAL DEMO / LANE KEEPING (วิ่งตามเส้นทาง Demo ปกติ)
            speed_cmd = desired_speed;
            steering_cmd = desired_steering;
            
            % ตรวจจับสิ่งกีดขวางด้านหน้าในระยะ < 1.20m (120 ซม.)
            if min_front < 1.20
                fsm_state = 1; % เริ่มเบี่ยงออกซ้ายทันที
                state_timer = 0;
                if min_left > 0.60 || min_left >= min_right
                    avoid_dir = 1;  % เบี่ยงซ้าย
                else
                    avoid_dir = -1; % เบี่ยงขวา
                end
            end
            
        case 1 % AVOIDING (หักเลี้ยวซ้ายเบี่ยงออก)
            state_timer = state_timer + dt;
            speed_cmd = 0.20;
            steering_cmd = -avoid_dir * steer_angle; % หักพวงมาลัยหลบออกซ้าย
            if min_front > 1.40 && state_timer >= avoid_time
                fsm_state = 2; % เปลี่ยนเป็นแซง
                state_timer = 0;
            end
            
        case 2 % PASSING (ขับแซงขนานเลนซ้าย)
            state_timer = state_timer + dt;
            speed_cmd = 0.22;
            steering_cmd = desired_steering * 0.5; % ขับตามแนวเลนเดิมประคอง
            if min_right > 0.70 && state_timer >= pass_time
                fsm_state = 3; % เปลี่ยนเป็นหักกลับเข้าเลน
                state_timer = 0;
            end
            
        case 3 % RETURNING (หักขวากลับเข้าเลนเดิม)
            state_timer = state_timer + dt;
            speed_cmd = 0.20;
            steering_cmd = avoid_dir * steer_angle; % หักพวงมาลัยขวากลับเข้าเลน
            if state_timer >= return_time
                fsm_state = 0; % กลับเข้าโหมดวิ่งตาม Demo ปกติ
                state_timer = 0;
            end
            
        otherwise
            speed_cmd = desired_speed;
            steering_cmd = desired_steering;
            fsm_state = 0;
    end
end
