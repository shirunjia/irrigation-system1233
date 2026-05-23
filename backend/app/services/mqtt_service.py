import paho.mqtt.client as mqtt
import json
import threading
from datetime import datetime
from app.config import Config
from app.models.device import Device
from app.models.sensor_data import SensorData
from app.models.alarm import Alarm
from app import db

# MQTT 主题定义
TOPIC_DATA_REPORT = 'irrigation/devices/+/data'  # 设备数据上报
TOPIC_STATUS_REPORT = 'irrigation/devices/+/status'  # 设备状态上报
TOPIC_COMMAND = 'irrigation/devices/{}/command'  # 控制命令下发
TOPIC_COMMAND_RESPONSE = 'irrigation/devices/{}/command/response'  # 命令响应

# 全局 MQTT 客户端
mqtt_client = None
flask_app = None


def on_connect(client, userdata, flags, rc):
    """连接回调"""
    if rc == 0:
        print('MQTT 连接成功')
        # 订阅设备数据上报主题
        client.subscribe(TOPIC_DATA_REPORT)
        client.subscribe(TOPIC_STATUS_REPORT)
        print(f'已订阅主题: {TOPIC_DATA_REPORT}, {TOPIC_STATUS_REPORT}')
    else:
        print(f'MQTT 连接失败，返回码: {rc}')


def on_disconnect(client, userdata, rc):
    """断开连接回调"""
    print(f'MQTT 连接断开，返回码: {rc}')


def on_message(client, userdata, msg):
    """消息接收回调"""
    try:
        topic = msg.topic
        payload = json.loads(msg.payload.decode('utf-8'))

        print(f'收到消息 - 主题: {topic}')

        # 解析设备 ID
        parts = topic.split('/')
        if len(parts) >= 3:
            device_id = parts[2]

            if 'data' in topic:
                handle_device_data(device_id, payload)
            elif 'status' in topic:
                handle_device_status(device_id, payload)

    except Exception as e:
        print(f'处理消息异常: {e}')


def handle_device_data(device_id, payload):
    """处理设备上报的传感器数据"""
    with flask_app.app_context():
        try:
            # 查找设备
            device = Device.query.filter_by(device_id=device_id).first()
            if not device:
                print(f'设备不存在: {device_id}')
                return

            # 解析传感器数据
            sensor_data = SensorData(
                device_id=device.id,
                soil_moisture=payload.get('soil_moisture'),
                temperature=payload.get('temperature'),
                humidity=payload.get('humidity'),
                light_intensity=payload.get('light_intensity'),
                soil_temperature=payload.get('soil_temperature'),
                timestamp=datetime.now(),
                raw_data=payload
            )

            db.session.add(sensor_data)

            # 更新设备最后在线时间
            device.last_online = datetime.now()
            device.status = 'online'

            db.session.commit()
            print(f'设备数据已保存: {device_id}')

            # 检查是否需要触发报警
            check_alarm(device, sensor_data)

        except Exception as e:
            db.session.rollback()
            print(f'处理设备数据异常: {e}')


def handle_device_status(device_id, payload):
    """处理设备状态上报"""
    with flask_app.app_context():
        try:
            device = Device.query.filter_by(device_id=device_id).first()
            if not device:
                return

            # 更新设备状态
            device.status = payload.get('status', 'offline')
            device.battery = payload.get('battery', device.battery)
            device.last_online = datetime.now()

            db.session.commit()
            print(f'设备状态已更新: {device_id} - {device.status}')

            # 设备离线报警
            if device.status == 'offline':
                create_alarm(
                    device_id=device.id,
                    level='critical',
                    type='device',
                    message=f'设备 {device.name} 已离线',
                    value='-',
                    threshold='-'
                )

        except Exception as e:
            db.session.rollback()
            print(f'处理设备状态异常: {e}')


def check_alarm(device, sensor_data):
    """检查传感器数据是否触发报警"""
    # 湿度报警
    if sensor_data.soil_moisture is not None:
        if sensor_data.soil_moisture < 20:
            create_alarm(
                device_id=device.id,
                level='critical',
                type='humidity',
                message=f'土壤湿度严重不足',
                value=f'{sensor_data.soil_moisture}%',
                threshold='20%'
            )
        elif sensor_data.soil_moisture < 30:
            create_alarm(
                device_id=device.id,
                level='warning',
                type='humidity',
                message=f'土壤湿度偏低',
                value=f'{sensor_data.soil_moisture}%',
                threshold='30%'
            )

    # 温度报警
    if sensor_data.temperature is not None:
        if sensor_data.temperature > 35:
            create_alarm(
                device_id=device.id,
                level='warning',
                type='temperature',
                message=f'温度异常升高',
                value=f'{sensor_data.temperature}°C',
                threshold='35°C'
            )


def create_alarm(device_id, level, type, message, value, threshold):
    """创建报警记录"""
    try:
        alarm = Alarm(
            device_id=device_id,
            level=level,
            type=type,
            message=message,
            value=value,
            threshold=threshold,
            status='unhandled'
        )
        db.session.add(alarm)
        db.session.commit()
        print(f'报警已创建: {message}')
    except Exception as e:
        db.session.rollback()
        print(f'创建报警异常: {e}')


def send_command(device_id, command_name, paras):
    """发送控制命令到设备"""
    if mqtt_client:
        topic = TOPIC_COMMAND.format(device_id)
        payload = {
            'command': command_name,
            'paras': paras,
            'timestamp': datetime.now().isoformat()
        }

        result = mqtt_client.publish(topic, json.dumps(payload))
        if result.rc == mqtt.MQTT_ERR_SUCCESS:
            print(f'命令已发送: {device_id} - {command_name}')
            return True
        else:
            print(f'命令发送失败: {result.rc}')
            return False
    return False


def start_mqtt(app):
    """启动 MQTT 服务"""
    global mqtt_client, flask_app

    flask_app = app

    mqtt_client = mqtt.Client(client_id='irrigation_server')

    # 设置认证（如果有）
    if Config.MQTT_USERNAME:
        mqtt_client.username_pw_set(Config.MQTT_USERNAME, Config.MQTT_PASSWORD)

    # 设置回调
    mqtt_client.on_connect = on_connect
    mqtt_client.on_disconnect = on_disconnect
    mqtt_client.on_message = on_message

    # 连接 MQTT 服务器
    try:
        mqtt_client.connect(Config.MQTT_BROKER, Config.MQTT_PORT, 60)
        mqtt_client.loop_start()
        print(f'MQTT 服务已启动，连接到 {Config.MQTT_BROKER}:{Config.MQTT_PORT}')
    except Exception as e:
        print(f'MQTT 连接失败: {e}')


def stop_mqtt():
    """停止 MQTT 服务"""
    global mqtt_client
    if mqtt_client:
        mqtt_client.loop_stop()
        mqtt_client.disconnect()
        print('MQTT 服务已停止')
