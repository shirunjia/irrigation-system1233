from flask import Blueprint, request, jsonify
from datetime import datetime
from app.models.irrigation import IrrigationPlan, IrrigationHistory
from app.models.device import Device
from app.services.mqtt_service import send_command
from app import db

irrigation_bp = Blueprint('irrigation', __name__)


@irrigation_bp.route('/plans', methods=['GET'])
def get_plans():
    """获取灌溉计划列表"""
    try:
        plans = IrrigationPlan.query.order_by(IrrigationPlan.created_at.desc()).all()

        return jsonify({
            'code': 200,
            'data': [p.to_dict() for p in plans]
        })

    except Exception as e:
        return jsonify({'code': 500, 'message': str(e)}), 500


@irrigation_bp.route('/plans', methods=['POST'])
def create_plan():
    """创建灌溉计划"""
    try:
        data = request.get_json()

        plan = IrrigationPlan(
            name=data.get('name'),
            device_id=data.get('deviceId'),
            mode=data.get('mode'),
            schedule_time=datetime.strptime(data['scheduleTime'], '%H:%M').time() if data.get('scheduleTime') else None,
            duration=data.get('duration'),
            threshold=data.get('threshold'),
            status='active' if data.get('active', True) else 'inactive'
        )

        db.session.add(plan)
        db.session.commit()

        return jsonify({
            'code': 200,
            'data': plan.to_dict(),
            'message': '计划创建成功'
        })

    except Exception as e:
        db.session.rollback()
        return jsonify({'code': 500, 'message': str(e)}), 500


@irrigation_bp.route('/plans/<int:id>', methods=['PUT'])
def update_plan(id):
    """更新灌溉计划"""
    try:
        plan = IrrigationPlan.query.get(id)
        if not plan:
            return jsonify({'code': 404, 'message': '计划不存在'}), 404

        data = request.get_json()

        if 'name' in data:
            plan.name = data['name']
        if 'deviceId' in data:
            plan.device_id = data['deviceId']
        if 'mode' in data:
            plan.mode = data['mode']
        if 'scheduleTime' in data:
            plan.schedule_time = datetime.strptime(data['scheduleTime'], '%H:%M').time() if data['scheduleTime'] else None
        if 'duration' in data:
            plan.duration = data['duration']
        if 'threshold' in data:
            plan.threshold = data['threshold']
        if 'active' in data:
            plan.status = 'active' if data['active'] else 'inactive'

        db.session.commit()

        return jsonify({
            'code': 200,
            'data': plan.to_dict(),
            'message': '计划更新成功'
        })

    except Exception as e:
        db.session.rollback()
        return jsonify({'code': 500, 'message': str(e)}), 500


@irrigation_bp.route('/plans/<int:id>', methods=['DELETE'])
def delete_plan(id):
    """删除灌溉计划"""
    try:
        plan = IrrigationPlan.query.get(id)
        if not plan:
            return jsonify({'code': 404, 'message': '计划不存在'}), 404

        db.session.delete(plan)
        db.session.commit()

        return jsonify({
            'code': 200,
            'message': '计划删除成功'
        })

    except Exception as e:
        db.session.rollback()
        return jsonify({'code': 500, 'message': str(e)}), 500


@irrigation_bp.route('/control/<int:device_id>', methods=['POST'])
def control_irrigation(device_id):
    """手动控制灌溉"""
    try:
        device = Device.query.get(device_id)
        if not device:
            return jsonify({'code': 404, 'message': '设备不存在'}), 404

        data = request.get_json()
        action = data.get('action')  # start/stop
        duration = data.get('duration', 30)  # 分钟

        # 发送控制命令
        command_paras = {
            'action': action,
            'duration': duration * 60 if action == 'start' else 0
        }

        success = send_command(device.device_id, 'irrigation_control', command_paras)

        if success:
            # 记录灌溉历史
            if action == 'start':
                history = IrrigationHistory(
                    device_id=device_id,
                    type='manual',
                    start_time=datetime.now(),
                    duration=duration,
                    status='in_progress'
                )
                db.session.add(history)
                db.session.commit()

            return jsonify({
                'code': 200,
                'message': f'灌溉{action}命令已发送'
            })
        else:
            return jsonify({
                'code': 500,
                'message': '命令发送失败'
            }), 500

    except Exception as e:
        db.session.rollback()
        return jsonify({'code': 500, 'message': str(e)}), 500


@irrigation_bp.route('/history', methods=['GET'])
def get_history():
    """获取灌溉历史"""
    try:
        page = request.args.get('page', 1, type=int)
        page_size = request.args.get('pageSize', 10, type=int)
        device_id = request.args.get('deviceId', type=int)

        query = IrrigationHistory.query

        if device_id:
            query = query.filter_by(device_id=device_id)

        total = query.count()
        history = query.order_by(IrrigationHistory.start_time.desc()).offset(
            (page - 1) * page_size
        ).limit(page_size).all()

        return jsonify({
            'code': 200,
            'data': {
                'list': [h.to_dict() for h in history],
                'total': total,
                'page': page,
                'pageSize': page_size
            }
        })

    except Exception as e:
        return jsonify({'code': 500, 'message': str(e)}), 500


@irrigation_bp.route('/stats', methods=['GET'])
def get_irrigation_stats():
    """获取灌溉统计"""
    try:
        # 今日灌溉次数
        today = datetime.now().date()
        today_count = IrrigationHistory.query.filter(
            IrrigationHistory.start_time >= datetime.combine(today, datetime.min.time())
        ).count()

        # 今日用水量
        today_water = db.session.query(
            db.func.sum(IrrigationHistory.water_used)
        ).filter(
            IrrigationHistory.start_time >= datetime.combine(today, datetime.min.time()),
            IrrigationHistory.water_used.isnot(None)
        ).scalar() or 0

        # 本周灌溉统计
        week_stats = []
        for i in range(7):
            date = today - __import__('datetime').timedelta(days=6 - i)
            count = IrrigationHistory.query.filter(
                IrrigationHistory.start_time >= datetime.combine(date, datetime.min.time()),
                IrrigationHistory.start_time < datetime.combine(date + __import__('datetime').timedelta(days=1), datetime.min.time())
            ).count()
            week_stats.append({
                'date': date.strftime('%Y-%m-%d'),
                'count': count
            })

        return jsonify({
            'code': 200,
            'data': {
                'todayCount': today_count,
                'todayWater': round(today_water, 1),
                'weekStats': week_stats
            }
        })

    except Exception as e:
        return jsonify({'code': 500, 'message': str(e)}), 500
