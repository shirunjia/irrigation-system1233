from flask import Blueprint, request, jsonify
from datetime import datetime, timedelta
from app.models.sensor_data import SensorData
from app.models.device import Device
from app import db

data_bp = Blueprint('data', __name__)


@data_bp.route('/<int:device_id>/latest', methods=['GET'])
def get_latest_data(device_id):
    """获取设备最新传感器数据"""
    try:
        data = SensorData.query.filter_by(
            device_id=device_id
        ).order_by(SensorData.timestamp.desc()).first()

        if not data:
            return jsonify({
                'code': 200,
                'data': None,
                'message': '暂无数据'
            })

        return jsonify({
            'code': 200,
            'data': data.to_dict()
        })

    except Exception as e:
        return jsonify({'code': 500, 'message': str(e)}), 500


@data_bp.route('/<int:device_id>/history', methods=['GET'])
def get_history_data(device_id):
    """获取设备历史传感器数据"""
    try:
        start_time = request.args.get('startTime')
        end_time = request.args.get('endTime')
        page = request.args.get('page', 1, type=int)
        page_size = request.args.get('pageSize', 50, type=int)

        query = SensorData.query.filter_by(device_id=device_id)

        # 时间范围过滤
        if start_time:
            query = query.filter(SensorData.timestamp >= datetime.strptime(start_time, '%Y-%m-%d %H:%M:%S'))
        if end_time:
            query = query.filter(SensorData.timestamp <= datetime.strptime(end_time, '%Y-%m-%d %H:%M:%S'))

        # 分页
        total = query.count()
        data_list = query.order_by(SensorData.timestamp.desc()).offset(
            (page - 1) * page_size
        ).limit(page_size).all()

        return jsonify({
            'code': 200,
            'data': {
                'list': [d.to_dict() for d in data_list],
                'total': total,
                'page': page,
                'pageSize': page_size
            }
        })

    except Exception as e:
        return jsonify({'code': 500, 'message': str(e)}), 500


@data_bp.route('/stats', methods=['GET'])
def get_data_stats():
    """获取数据统计"""
    try:
        # 设备总数
        total_devices = Device.query.count()

        # 在线设备数
        online_devices = Device.query.filter_by(status='online').count()

        # 今日数据量
        today = datetime.now().date()
        today_data_count = SensorData.query.filter(
            SensorData.timestamp >= datetime.combine(today, datetime.min.time())
        ).count()

        # 本周数据趋势
        week_data = []
        for i in range(7):
            date = today - timedelta(days=6 - i)
            count = SensorData.query.filter(
                SensorData.timestamp >= datetime.combine(date, datetime.min.time()),
                SensorData.timestamp < datetime.combine(date + timedelta(days=1), datetime.min.time())
            ).count()
            week_data.append({
                'date': date.strftime('%Y-%m-%d'),
                'count': count
            })

        return jsonify({
            'code': 200,
            'data': {
                'totalDevices': total_devices,
                'onlineDevices': online_devices,
                'todayDataCount': today_data_count,
                'weekDataTrend': week_data
            }
        })

    except Exception as e:
        return jsonify({'code': 500, 'message': str(e)}), 500


@data_bp.route('/moisture-trend', methods=['GET'])
def get_moisture_trend():
    """获取土壤湿度趋势"""
    try:
        device_id = request.args.get('deviceId', type=int)
        time_range = request.args.get('range', 'day')  # day/week/month

        if not device_id:
            return jsonify({'code': 400, 'message': '缺少设备ID'}), 400

        now = datetime.now()

        if time_range == 'day':
            start_time = now - timedelta(hours=24)
            interval = timedelta(hours=1)
        elif time_range == 'week':
            start_time = now - timedelta(days=7)
            interval = timedelta(days=1)
        else:  # month
            start_time = now - timedelta(days=30)
            interval = timedelta(days=1)

        # 获取数据
        data_list = SensorData.query.filter(
            SensorData.device_id == device_id,
            SensorData.timestamp >= start_time
        ).order_by(SensorData.timestamp.asc()).all()

        # 按时间间隔分组计算平均值
        trend_data = []
        current_start = start_time

        while current_start < now:
            current_end = current_start + interval

            # 获取该时间段的数据
            interval_data = [
                d for d in data_list
                if current_start <= d.timestamp < current_end
            ]

            if interval_data:
                avg_moisture = sum(d.soil_moisture or 0 for d in interval_data) / len(interval_data)
                trend_data.append({
                    'time': current_start.strftime('%H:%M' if time_range == 'day' else '%m-%d'),
                    'value': round(avg_moisture, 1)
                })

            current_start = current_end

        return jsonify({
            'code': 200,
            'data': trend_data
        })

    except Exception as e:
        return jsonify({'code': 500, 'message': str(e)}), 500
