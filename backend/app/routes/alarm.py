from flask import Blueprint, request, jsonify
from datetime import datetime
from app.models.alarm import Alarm
from app.models.device import Device
from app import db

alarm_bp = Blueprint('alarm', __name__)


@alarm_bp.route('', methods=['GET'])
def get_alarms():
    """获取报警列表"""
    try:
        page = request.args.get('page', 1, type=int)
        page_size = request.args.get('pageSize', 10, type=int)
        level = request.args.get('level', '')
        status = request.args.get('status', '')
        alarm_type = request.args.get('type', '')
        start_time = request.args.get('startTime')
        end_time = request.args.get('endTime')

        query = Alarm.query

        # 过滤条件
        if level:
            query = query.filter(Alarm.level == level)
        if status:
            query = query.filter(Alarm.status == status)
        if alarm_type:
            query = query.filter(Alarm.type == alarm_type)
        if start_time:
            query = query.filter(Alarm.created_at >= datetime.strptime(start_time, '%Y-%m-%d %H:%M:%S'))
        if end_time:
            query = query.filter(Alarm.created_at <= datetime.strptime(end_time, '%Y-%m-%d %H:%M:%S'))

        # 分页
        total = query.count()
        alarms = query.order_by(Alarm.created_at.desc()).offset(
            (page - 1) * page_size
        ).limit(page_size).all()

        return jsonify({
            'code': 200,
            'data': {
                'list': [a.to_dict() for a in alarms],
                'total': total,
                'page': page,
                'pageSize': page_size
            }
        })

    except Exception as e:
        return jsonify({'code': 500, 'message': str(e)}), 500


@alarm_bp.route('/<int:id>', methods=['GET'])
def get_alarm(id):
    """获取报警详情"""
    try:
        alarm = Alarm.query.get(id)
        if not alarm:
            return jsonify({'code': 404, 'message': '报警不存在'}), 404

        return jsonify({
            'code': 200,
            'data': alarm.to_dict()
        })

    except Exception as e:
        return jsonify({'code': 500, 'message': str(e)}), 500


@alarm_bp.route('/<int:id>/handle', methods=['PUT'])
def handle_alarm(id):
    """处理报警"""
    try:
        alarm = Alarm.query.get(id)
        if not alarm:
            return jsonify({'code': 404, 'message': '报警不存在'}), 404

        data = request.get_json() or {}

        alarm.status = 'handled'
        alarm.handle_time = datetime.now()
        alarm.handler = data.get('handler', '管理员')
        alarm.handle_remark = data.get('remark', '已手动处理')

        db.session.commit()

        return jsonify({
            'code': 200,
            'data': alarm.to_dict(),
            'message': '报警已处理'
        })

    except Exception as e:
        db.session.rollback()
        return jsonify({'code': 500, 'message': str(e)}), 500


@alarm_bp.route('/stats', methods=['GET'])
def get_alarm_stats():
    """获取报警统计"""
    try:
        # 报警总数
        total = Alarm.query.count()

        # 待处理报警数
        unhandled = Alarm.query.filter_by(status='unhandled').count()

        # 已处理报警数
        handled = Alarm.query.filter_by(status='handled').count()

        # 今日报警数
        today = datetime.now().date()
        today_count = Alarm.query.filter(
            Alarm.created_at >= datetime.combine(today, datetime.min.time())
        ).count()

        # 按级别统计
        level_stats = db.session.query(
            Alarm.level,
            db.func.count(Alarm.id)
        ).group_by(Alarm.level).all()

        # 按类型统计
        type_stats = db.session.query(
            Alarm.type,
            db.func.count(Alarm.id)
        ).group_by(Alarm.type).all()

        # 本周报警趋势
        week_stats = []
        for i in range(7):
            date = today - __import__('datetime').timedelta(days=6 - i)
            count = Alarm.query.filter(
                Alarm.created_at >= datetime.combine(date, datetime.min.time()),
                Alarm.created_at < datetime.combine(date + __import__('datetime').timedelta(days=1), datetime.min.time())
            ).count()
            week_stats.append({
                'date': date.strftime('%Y-%m-%d'),
                'count': count
            })

        return jsonify({
            'code': 200,
            'data': {
                'total': total,
                'unhandled': unhandled,
                'handled': handled,
                'todayCount': today_count,
                'levelStats': {level: count for level, count in level_stats},
                'typeStats': {type_: count for type_, count in type_stats},
                'weekStats': week_stats
            }
        })

    except Exception as e:
        return jsonify({'code': 500, 'message': str(e)}), 500


@alarm_bp.route('/batch-handle', methods=['POST'])
def batch_handle_alarms():
    """批量处理报警"""
    try:
        data = request.get_json()
        alarm_ids = data.get('ids', [])
        handler = data.get('handler', '管理员')
        remark = data.get('remark', '批量处理')

        alarms = Alarm.query.filter(Alarm.id.in_(alarm_ids)).all()

        for alarm in alarms:
            alarm.status = 'handled'
            alarm.handle_time = datetime.now()
            alarm.handler = handler
            alarm.handle_remark = remark

        db.session.commit()

        return jsonify({
            'code': 200,
            'message': f'已处理 {len(alarms)} 条报警'
        })

    except Exception as e:
        db.session.rollback()
        return jsonify({'code': 500, 'message': str(e)}), 500
