function [min_front, min_left, min_right] = LiDAR_Obstacle_Detector(Distances, Headings)
    % แปลงมุม Headings (0..2*pi) ให้เป็นช่วง [-pi, pi]
    angles = atan2(sin(Headings), cos(Headings));
    
    % กรองระยะ: ต้องมากกว่า 0.15m (ตัดสัญญาณรบกวนโครงรถ) และน้อยกว่า 6.0m
    valid = (Distances > 0.15) & (Distances < 6.0);
    
    front_mask = valid & (abs(angles) <= 30*pi/180);                       % ด้านหน้า -30 ถึง +30 องศา
    left_mask  = valid & (angles > 30*pi/180) & (angles <= 90*pi/180);     % ด้านซ้าย +30 ถึง +90 องศา
    right_mask = valid & (angles < -30*pi/180) & (angles >= -90*pi/180);   % ด้านขวา -90 ถึง -30 องศา
    
    if any(front_mask)
        min_front = min(Distances(front_mask));
    else
        min_front = 999.0;
    end
    
    if any(left_mask)
        min_left = min(Distances(left_mask));
    else
        min_left = 999.0;
    end
    
    if any(right_mask)
        min_right = min(Distances(right_mask));
    else
        min_right = 999.0;
    end
end
