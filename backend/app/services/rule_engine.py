import threading
import time
from datetime import datetime, timedelta
from apscheduler.schedulers.background import BackgroundScheduler
from app.models.device import Device
from app.models.sensor_data import SensorData
from app.models.irrigation import IrrigationPlan, IrrigationHistory
from app.services.mqtt_service import send_command
from app import db

# 全局调度器
scheduler = None
flask_app = None


def check_auto_irrigation():
    """检查自动灌溉规则"""
    with flask_app.app_context():
        try:
            # 获取所有自动模式的灌溉计划
            plans = IrrigationPlan.query.filter_by(
                mode='auto',
                status='active'
            ).all()

            for plan in plans:
                # 获取设备最新传感器数据
                latest_data = SensorData.query.filter_by(
                    device_id=plan.device_id
                ).order_by(SensorData.timestamp.desc()).first()

                if latest_data and latest_data.soil_moisture is not None:
                    # 检查是否低于阈值
                    if latest_data.soil_moisture < plan.threshold:
                        # 检查是否正在灌溉
                        active_irrigation = IrrigationHistory.query.filter_by(
                            device_id=plan.device_id,
                            status='in_progress'
                        ).first()

                        if not active_irrigation:
                            # 触发灌溉
                            trigger_irrigation(plan, 'auto')

        except Exception as e:
            print(f'检查自动灌溉规则异常: {e}')


def check_scheduled_irrigation():
    """检查定时灌溉计划"""
    with flask_app.app_context():
        try:
            current_time = datetime.now().time()
            current_hour = current_time.hour
            current_minute = current_time.minute

            # 获取所有定时模式的灌溉计划
            plans = IrrigationPlan.query.filter_by(
                mode='scheduled',
                status='active'
            ).all()

            for plan in plans:
                if plan.schedule_time:
                    # 检查是否到达执行时间
                    if (plan.schedule_time.hour == current_hour and
                            plan.schedule_time.minute == current_minute):

                        # 检查今天是否已经执行过
                        today = datetime.now().date()
                        executed_today = IrrigationHistory.query.filter(
                            IrrigationHistory.device_id == plan.device_id,
                            IrrigationHistory.plan_id == plan.id,
                            IrrigationHistory.start_time >= datetime.combine(today, datetime.min.time())
                        ).first()

                        if not executed_today:
                            trigger_irrigation(plan, 'scheduled')

        except Exception as e:
            print(f'检查定时灌溉计划异常: {e}')


def trigger_irrigation(plan, irrigation_type):
    """触发灌溉"""
    with flask_app.app_context():
        try:
            # 创建灌溉历史记录
            history = IrrigationHistory(
                device_id=plan.device_id,
                plan_id=plan.id,
                type=irrigation_type,
                start_time=datetime.now(),
                duration=plan.duration,
                status='in_progress'
            )
            db.session.add(history)
            db.session.commit()

            # 发送灌溉命令
            device = Device.query.get(plan.device_id)
            if device:
                command_paras = {
                    'action': 'start',
                    'duration': plan.duration * 60  # 转换为秒
                }

                success = send_command(device.device_id, 'irrigation_control', command_paras)

                if success:
                    print(f'灌溉已触发: {device.name} - {irrigation_type}模式')

                    # 设置定时器在灌溉结束后更新状态
                    timer = threading.Timer(
                        plan.duration * 60,
                        complete_irrigation,
                        args=[history.id]
                    )
                    timer.start()
                else:
                    # 命令发送失败，更新状态
                    history.status = 'failed'
                    db.session.commit()

        except Exception as e:
            db.session.rollback()
            print(f'触发灌溉异常: {e}')


def complete_irrigation(history_id):
    """完成灌溉"""
    with flask_app.app_context():
        try:
            history = IrrigationHistory.query.get(history_id)
            if history and history.status == 'in_progress':
                history.end_time = datetime.now()
                history.status = 'completed'
                # 计算用水量（假设每分钟 5 升）
                history.water_used = history.duration * 5
                db.session.commit()
                print(f'灌溉已完成: ID={history_id}')

        except Exception as e:
            db.session.rollback()
            print(f'完成灌溉异常: {e}')


def check_device_online_status():
    """检查设备在线状态"""
    with flask_app.app_context():
        try:
            # 获取所有设备
            devices = Device.query.filter(Device.status != 'offline').all()

            # 离线阈值：5 分钟
            threshold = datetime.now() - timedelta(minutes=5)

            for device in devices:
                if device.last_online and device.last_online < threshold:
                    device.status = 'offline'
                    print(f'设备离线: {device.name}')

            db.session.commit()

        except Exception as e:
            db.session.rollback()
            print(f'检查设备在线状态异常: {e}')


def start_rule_engine(app):
    """启动规则引擎"""
    global scheduler, flask_app

    flask_app = app

    scheduler = BackgroundScheduler()

    # 添加定时任务
    # 每分钟检查自动灌溉规则
    scheduler.add_job(
        check_auto_irrigation,
        'interval',
        minutes=1,
        id='check_auto_irrigation'
    )

    # 每分钟检查定时灌溉计划
    scheduler.add_job(
        check_scheduled_irrigation,
        'interval',
        minutes=1,
        id='check_scheduled_irrigation'
    )

    # 每 5 分钟检查设备在线状态
    scheduler.add_job(
        check_device_online_status,
        'interval',
        minutes=5,
        id='check_device_online_status'
    )

    scheduler.start()
    print('规则引擎已启动')


def stop_rule_engine():
    """停止规则引擎"""
    global scheduler
    if scheduler:
        scheduler.shutdown()
        print('规则引擎已停止')
