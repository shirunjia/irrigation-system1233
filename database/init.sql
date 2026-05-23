-- 智能灌溉系统数据库初始化脚本

-- 创建数据库
CREATE DATABASE IF NOT EXISTS irrigation DEFAULT CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;

USE irrigation;

-- 设备表
CREATE TABLE IF NOT EXISTS devices (
    id INT PRIMARY KEY AUTO_INCREMENT,
    device_id VARCHAR(50) NOT NULL UNIQUE COMMENT '设备ID',
    name VARCHAR(100) NOT NULL COMMENT '设备名称',
    type VARCHAR(50) NOT NULL COMMENT '设备类型',
    location VARCHAR(200) COMMENT '安装位置',
    status VARCHAR(20) DEFAULT 'offline' COMMENT '设备状态',
    battery INT DEFAULT 100 COMMENT '电量',
    last_online DATETIME COMMENT '最后在线时间',
    huawei_device_id VARCHAR(100) COMMENT '华为云设备ID',
    remark TEXT COMMENT '备注',
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    INDEX idx_device_id (device_id),
    INDEX idx_status (status),
    INDEX idx_type (type)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='设备表';

-- 传感器数据表
CREATE TABLE IF NOT EXISTS sensor_data (
    id INT PRIMARY KEY AUTO_INCREMENT,
    device_id INT NOT NULL COMMENT '设备ID',
    soil_moisture FLOAT COMMENT '土壤湿度(%)',
    temperature FLOAT COMMENT '温度(°C)',
    humidity FLOAT COMMENT '空气湿度(%)',
    light_intensity FLOAT COMMENT '光照强度(lux)',
    soil_temperature FLOAT COMMENT '土壤温度(°C)',
    timestamp DATETIME DEFAULT CURRENT_TIMESTAMP COMMENT '采集时间',
    raw_data JSON COMMENT '原始数据',
    FOREIGN KEY (device_id) REFERENCES devices(id) ON DELETE CASCADE,
    INDEX idx_device_timestamp (device_id, timestamp),
    INDEX idx_timestamp (timestamp)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='传感器数据表';

-- 灌溉计划表
CREATE TABLE IF NOT EXISTS irrigation_plans (
    id INT PRIMARY KEY AUTO_INCREMENT,
    name VARCHAR(100) NOT NULL COMMENT '计划名称',
    device_id INT NOT NULL COMMENT '设备ID',
    mode VARCHAR(20) NOT NULL COMMENT '模式: auto/scheduled',
    schedule_time TIME COMMENT '定时时间',
    duration INT NOT NULL COMMENT '灌溉时长(分钟)',
    threshold FLOAT COMMENT '湿度阈值(%)',
    status VARCHAR(20) DEFAULT 'active' COMMENT '状态: active/inactive',
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    FOREIGN KEY (device_id) REFERENCES devices(id) ON DELETE CASCADE,
    INDEX idx_mode (mode),
    INDEX idx_status (status)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='灌溉计划表';

-- 灌溉历史表
CREATE TABLE IF NOT EXISTS irrigation_history (
    id INT PRIMARY KEY AUTO_INCREMENT,
    device_id INT NOT NULL COMMENT '设备ID',
    plan_id INT COMMENT '计划ID',
    type VARCHAR(20) NOT NULL COMMENT '类型: manual/auto/scheduled',
    start_time DATETIME NOT NULL COMMENT '开始时间',
    end_time DATETIME COMMENT '结束时间',
    duration INT COMMENT '实际时长(分钟)',
    water_used FLOAT COMMENT '用水量(L)',
    status VARCHAR(20) DEFAULT 'in_progress' COMMENT '状态: in_progress/completed',
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (device_id) REFERENCES devices(id) ON DELETE CASCADE,
    FOREIGN KEY (plan_id) REFERENCES irrigation_plans(id) ON DELETE SET NULL,
    INDEX idx_device (device_id),
    INDEX idx_start_time (start_time),
    INDEX idx_status (status)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='灌溉历史表';

-- 报警表
CREATE TABLE IF NOT EXISTS alarms (
    id INT PRIMARY KEY AUTO_INCREMENT,
    device_id INT NOT NULL COMMENT '设备ID',
    level VARCHAR(20) NOT NULL COMMENT '级别: critical/warning/info',
    type VARCHAR(50) NOT NULL COMMENT '类型: humidity/temperature/device/communication',
    message VARCHAR(500) NOT NULL COMMENT '报警信息',
    value VARCHAR(50) COMMENT '当前值',
    threshold VARCHAR(50) COMMENT '阈值',
    status VARCHAR(20) DEFAULT 'unhandled' COMMENT '状态: unhandled/handled',
    handle_time DATETIME COMMENT '处理时间',
    handler VARCHAR(50) COMMENT '处理人',
    handle_remark TEXT COMMENT '处理说明',
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (device_id) REFERENCES devices(id) ON DELETE CASCADE,
    INDEX idx_level (level),
    INDEX idx_type (type),
    INDEX idx_status (status),
    INDEX idx_created_at (created_at)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='报警表';

-- 插入示例数据

-- 示例设备
INSERT INTO devices (device_id, name, type, location, status, battery, last_online) VALUES
('BP-001', 'A区-1号传感器', 'soil_sensor', 'A区-1号地块', 'online', 85, NOW()),
('BP-002', 'A区-2号传感器', 'soil_sensor', 'A区-2号地块', 'online', 72, NOW()),
('BP-003', 'B区-1号传感器', 'soil_sensor', 'B区-1号地块', 'offline', 45, DATE_SUB(NOW(), INTERVAL 2 HOUR)),
('WS-001', '中央气象站', 'weather_station', '园区中心', 'online', 100, NOW()),
('IC-001', 'A区灌溉控制器', 'irrigation_controller', 'A区泵房', 'online', 100, NOW()),
('IC-002', 'B区灌溉控制器', 'irrigation_controller', 'B区泵房', 'fault', 100, DATE_SUB(NOW(), INTERVAL 4 HOUR)),
('WP-001', '1号水泵', 'water_pump', '水源井1', 'online', 100, NOW()),
('BP-004', 'C区-1号传感器', 'soil_sensor', 'C区-1号地块', 'maintenance', 30, DATE_SUB(NOW(), INTERVAL 1 DAY));

-- 示例传感器数据
INSERT INTO sensor_data (device_id, soil_moisture, temperature, humidity, timestamp) VALUES
(1, 65, 28, 45, NOW()),
(1, 62, 27, 46, DATE_SUB(NOW(), INTERVAL 1 HOUR)),
(1, 58, 29, 44, DATE_SUB(NOW(), INTERVAL 2 HOUR)),
(2, 70, 28, 48, NOW()),
(2, 68, 27, 49, DATE_SUB(NOW(), INTERVAL 1 HOUR)),
(4, NULL, 32, 55, NOW()),
(4, NULL, 31, 56, DATE_SUB(NOW(), INTERVAL 1 HOUR));

-- 示例灌溉计划
INSERT INTO irrigation_plans (name, device_id, mode, schedule_time, duration, threshold, status) VALUES
('A区自动灌溉', 5, 'auto', NULL, 30, 40, 'active'),
('B区定时灌溉', 6, 'scheduled', '06:00:00', 45, NULL, 'active'),
('C区夜间灌溉', 5, 'scheduled', '22:00:00', 60, NULL, 'inactive');

-- 示例灌溉历史
INSERT INTO irrigation_history (device_id, plan_id, type, start_time, end_time, duration, water_used, status) VALUES
(5, 1, 'auto', DATE_SUB(NOW(), INTERVAL 8 HOUR), DATE_SUB(NOW(), INTERVAL 7 HOUR), 30, 150, 'completed'),
(6, 2, 'scheduled', DATE_SUB(NOW(), INTERVAL 7 HOUR), DATE_SUB(NOW(), INTERVAL 6 HOUR), 45, 220, 'completed'),
(5, NULL, 'manual', DATE_SUB(NOW(), INTERVAL 1 DAY), DATE_SUB(NOW(), INTERVAL 23 HOUR), 20, 100, 'completed');

-- 示例报警
INSERT INTO alarms (device_id, level, type, message, value, threshold, status, handle_time, handler) VALUES
(1, 'critical', 'humidity', '土壤湿度严重不足，低于临界值', '18%', '20%', 'unhandled', NULL, NULL),
(3, 'warning', 'temperature', '温度异常升高，超出正常范围', '38°C', '35°C', 'unhandled', NULL, NULL),
(6, 'critical', 'device', '设备离线超过1小时', '-', '-', 'unhandled', NULL, NULL),
(2, 'info', 'humidity', '土壤湿度偏低，建议灌溉', '32%', '35%', 'handled', DATE_SUB(NOW(), INTERVAL 2 HOUR), '张三'),
(3, 'warning', 'communication', '通信信号弱，数据上报延迟', '20ms', '10ms', 'handled', DATE_SUB(NOW(), INTERVAL 3 HOUR), '李四');
