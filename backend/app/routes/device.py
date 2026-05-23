from flask import Blueprint, request, jsonify
from app.models.device import Device
from app.models.sensor_data import SensorData
from app.services.huawei_iot import huawei_iot
from app.services.mqtt_service import send_command
from app import db

device_bp = Blueprint('device', __name__)


@device_bp.route('', methods=['GET'])
def get_devices():
    """获取设备列表"""
    try:
        page = request.args.get('page', 1, type=int)
        page_size = request.args.get('pageSize', 10, type=int)
        keyword = request.args.get('keyword', '')
        status = request.args.get('status', '')
        device_type = request.args.get('type', '')

        query = Device.query

        # 搜索过滤
        if keyword:
            query = query.filter(
                (Device.name.like(f'%{keyword}%')) |
                (Device.device_id.like(f'%{keyword}%'))
            )

        if status:
            query = query.filter(Device.status == status)

        if device_type:
            query = query.filter(Device.type == device_type)

        # 分页
        total = query.count()
        devices = query.order_by(Device.created_at.desc()).offset(
            (page - 1) * page_size
        ).limit(page_size).all()

        return jsonify({
            'code': 200,
            'data': {
                'list': [d.to_dict() for d in devices],
                'total': total,
                'page': page,
                'pageSize': page_size
            }
        })

    except Exception as e:
        return jsonify({'code': 500, 'message': str(e)}), 500


@device_bp.route('/<int:id>', methods=['GET'])
def get_device(id):
    """获取设备详情"""
    try:
        device = Device.query.get(id)
        if not device:
            return jsonify({'code': 404, 'message': '设备不存在'}), 404

        return jsonify({
            'code': 200,
            'data': device.to_dict()
        })

    except Exception as e:
        return jsonify({'code': 500, 'message': str(e)}), 500


@device_bp.route('', methods=['POST'])
def create_device():
    """创建设备"""
    try:
        data = request.get_json()

        # 检查设备 ID 是否已存在
        existing = Device.query.filter_by(device_id=data.get('deviceId')).first()
        if existing:
            return jsonify({'code': 400, 'message': '设备ID已存在'}), 400

        # 创建设备
        device = Device(
            device_id=data.get('deviceId'),
            name=data.get('name'),
            type=data.get('type'),
            location=data.get('location'),
            remark=data.get('remark'),
            status='offline'
        )

        db.session.add(device)
        db.session.commit()

        # 注册到华为云 IoTDA
        if huawei_iot.product_id:
            result = huawei_iot.register_device(
                device_id=f'irrigation_{device.device_id}',
                node_id=device.device_id,
                name=device.name,
                description=device.remark or ''
            )

            if result.get('success'):
                device.huawei_device_id = result.get('device_id')
                db.session.commit()

        return jsonify({
            'code': 200,
            'data': device.to_dict(),
            'message': '设备创建成功'
        })

    except Exception as e:
        db.session.rollback()
        return jsonify({'code': 500, 'message': str(e)}), 500


@device_bp.route('/<int:id>', methods=['PUT'])
def update_device(id):
    """更新设备"""
    try:
        device = Device.query.get(id)
        if not device:
            return jsonify({'code': 404, 'message': '设备不存在'}), 404

        data = request.get_json()

        # 更新字段
        if 'name' in data:
            device.name = data['name']
        if 'type' in data:
            device.type = data['type']
        if 'location' in data:
            device.location = data['location']
        if 'remark' in data:
            device.remark = data['remark']
        if 'status' in data:
            device.status = data['status']

        db.session.commit()

        return jsonify({
            'code': 200,
            'data': device.to_dict(),
            'message': '设备更新成功'
        })

    except Exception as e:
        db.session.rollback()
        return jsonify({'code': 500, 'message': str(e)}), 500


@device_bp.route('/<int:id>', methods=['DELETE'])
def delete_device(id):
    """删除设备"""
    try:
        device = Device.query.get(id)
        if not device:
            return jsonify({'code': 404, 'message': '设备不存在'}), 404

        # 从华为云 IoTDA 删除
        if device.huawei_device_id:
            huawei_iot.delete_device(device.huawei_device_id)

        db.session.delete(device)
        db.session.commit()

        return jsonify({
            'code': 200,
            'message': '设备删除成功'
        })

    except Exception as e:
        db.session.rollback()
        return jsonify({'code': 500, 'message': str(e)}), 500


@device_bp.route('/<int:id>/command', methods=['POST'])
def send_device_command(id):
    """发送设备命令"""
    try:
        device = Device.query.get(id)
        if not device:
            return jsonify({'code': 404, 'message': '设备不存在'}), 404

        data = request.get_json()
        command = data.get('command')
        paras = data.get('paras', {})

        # 通过 MQTT 发送命令
        success = send_command(device.device_id, command, paras)

        if success:
            return jsonify({
                'code': 200,
                'message': '命令已发送'
            })
        else:
            return jsonify({
                'code': 500,
                'message': '命令发送失败'
            }), 500

    except Exception as e:
        return jsonify({'code': 500, 'message': str(e)}), 500


@device_bp.route('/<string:device_id>/properties', methods=['GET'])
def get_device_properties(device_id):
    """获取设备最新属性（传感器数据）"""
    try:
        device = Device.query.filter_by(device_id=device_id).first()
        if not device:
            return jsonify({'code': 404, 'message': '设备不存在'}), 404

        data = SensorData.query.filter_by(
            device_id=device.id
        ).order_by(SensorData.timestamp.desc()).first()

        if not data:
            return jsonify({
                'code': 200,
                'data': None
            })

        return jsonify({
            'code': 200,
            'data': {
                'humidity': data.soil_moisture,
                'temperature': data.temperature,
                'airHumidity': data.humidity,
                'luminance': data.light_intensity,
                'soilTemperature': data.soil_temperature,
                'lightStatus': False,
                'timestamp': data.timestamp.strftime('%Y-%m-%d %H:%M:%S')
            }
        })

    except Exception as e:
        return jsonify({'code': 500, 'message': str(e)}), 500
