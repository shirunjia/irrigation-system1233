import sys
import os
sys.path.insert(0, os.path.dirname(__file__))

from app import create_app, db
from app.models.device import Device
from app.models.sensor_data import SensorData
from app.models.irrigation import IrrigationPlan, IrrigationHistory
from app.models.alarm import Alarm
from datetime import datetime, timedelta
import random

app = create_app()

with app.app_context():
    # 清空旧数据
    db.drop_all()
    db.create_all()

    # ========== 设备 ==========
    devices = [
        Device(device_id='DEV-001', name='A区土壤传感器', type='sensor', location='A区-1号田', status='online', battery=85, last_online=datetime.now()),
        Device(device_id='DEV-002', name='B区土壤传感器', type='sensor', location='B区-2号田', status='online', battery=72, last_online=datetime.now()),
        Device(device_id='DEV-003', name='C区土壤传感器', type='sensor', location='C区-3号田', status='offline', battery=15, last_online=datetime.now() - timedelta(hours=3)),
        Device(device_id='DEV-004', name='A区灌溉阀门', type='valve', location='A区-1号田', status='online', battery=90, last_online=datetime.now()),
        Device(device_id='DEV-005', name='B区灌溉阀门', type='valve', location='B区-2号田', status='online', battery=65, last_online=datetime.now()),
        Device(device_id='DEV-006', name='C区灌溉阀门', type='valve', location='C区-3号田', status='offline', battery=20, last_online=datetime.now() - timedelta(days=1)),
    ]
    db.session.add_all(devices)
    db.session.flush()

    # ========== 传感器数据（最近7天） ==========
    sensor_records = []
    for day in range(7):
        for hour in [6, 9, 12, 15, 18, 21]:
            ts = datetime.now() - timedelta(days=day, hours=datetime.now().hour - hour)
            for dev in [devices[0], devices[1], devices[2]]:
                base_moisture = {'DEV-001': 45, 'DEV-002': 55, 'DEV-003': 38}[dev.device_id]
                sensor_records.append(SensorData(
                    device_id=dev.id,
                    soil_moisture=round(base_moisture + random.uniform(-15, 15), 1),
                    temperature=round(25 + random.uniform(-8, 10), 1),
                    humidity=round(60 + random.uniform(-20, 20), 1),
                    light_intensity=round(5000 + random.uniform(-3000, 5000)),
                    soil_temperature=round(20 + random.uniform(-5, 8), 1),
                    timestamp=ts
                ))
    db.session.add_all(sensor_records)

    # ========== 灌溉计划 ==========
    plans = [
        IrrigationPlan(name='A区早间灌溉', device_id=devices[3].id, mode='scheduled', schedule_time=datetime.strptime('06:00', '%H:%M').time(), duration=30, threshold=40, status='active'),
        IrrigationPlan(name='B区自动灌溉', device_id=devices[4].id, mode='auto', duration=20, threshold=45, status='active'),
        IrrigationPlan(name='C区定时灌溉', device_id=devices[5].id, mode='scheduled', schedule_time=datetime.strptime('17:00', '%H:%M').time(), duration=25, threshold=35, status='inactive'),
    ]
    db.session.add_all(plans)
    db.session.flush()

    # ========== 灌溉历史（最近7天） ==========
    history_records = []
    for day in range(7):
        dt = datetime.now() - timedelta(days=day)
        # A区 - 定时灌溉
        start = dt.replace(hour=6, minute=0, second=0, microsecond=0)
        history_records.append(IrrigationHistory(
            device_id=devices[3].id, plan_id=plans[0].id, type='scheduled',
            start_time=start, end_time=start + timedelta(minutes=30),
            duration=30, water_used=round(random.uniform(80, 120), 1), status='completed'
        ))
        # B区 - 自动灌溉（部分天数）
        if day % 2 == 0:
            start2 = dt.replace(hour=14, minute=0, second=0, microsecond=0)
            history_records.append(IrrigationHistory(
                device_id=devices[4].id, plan_id=plans[1].id, type='auto',
                start_time=start2, end_time=start2 + timedelta(minutes=20),
                duration=20, water_used=round(random.uniform(50, 80), 1), status='completed'
            ))
        # 手动灌溉
        if day == 1:
            start3 = dt.replace(hour=10, minute=30, second=0, microsecond=0)
            history_records.append(IrrigationHistory(
                device_id=devices[3].id, type='manual',
                start_time=start3, end_time=start3 + timedelta(minutes=15),
                duration=15, water_used=45.5, status='completed'
            ))
    db.session.add_all(history_records)

    # ========== 报警记录 ==========
    alarms = [
        Alarm(device_id=devices[2].id, level='critical', type='device', message='C区土壤传感器离线超过3小时', value='offline', threshold='1小时', status='unhandled'),
        Alarm(device_id=devices[0].id, level='warning', type='humidity', message='A区土壤湿度过低', value='28%', threshold='40%', status='handled', handle_time=datetime.now() - timedelta(hours=2), handler='张三', handle_remark='已启动紧急灌溉'),
        Alarm(device_id=devices[1].id, level='info', type='temperature', message='B区温度偏高', value='36°C', threshold='35°C', status='handled', handle_time=datetime.now() - timedelta(hours=5), handler='李四', handle_remark='持续观察中'),
        Alarm(device_id=devices[5].id, level='warning', type='communication', message='C区阀门通信不稳定', value='丢包率15%', threshold='5%', status='unhandled'),
        Alarm(device_id=devices[0].id, level='info', type='humidity', message='A区湿度恢复正常', value='52%', threshold='40%', status='handled', handle_time=datetime.now() - timedelta(days=1), handler='系统', handle_remark='自动恢复'),
    ]
    db.session.add_all(alarms)

    db.session.commit()
    print('虚拟数据插入成功！')
    print(f'  设备: {len(devices)} 条')
    print(f'  传感器数据: {len(sensor_records)} 条')
    print(f'  灌溉计划: {len(plans)} 条')
    print(f'  灌溉历史: {len(history_records)} 条')
    print(f'  报警记录: {len(alarms)} 条')
