from app import db
from datetime import datetime

class IrrigationPlan(db.Model):
    __tablename__ = 'irrigation_plans'

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    name = db.Column(db.String(100), nullable=False, comment='计划名称')
    device_id = db.Column(db.Integer, db.ForeignKey('devices.id'), nullable=False)
    mode = db.Column(db.String(20), nullable=False, comment='模式: auto/scheduled')
    schedule_time = db.Column(db.Time, comment='定时时间')
    duration = db.Column(db.Integer, nullable=False, comment='灌溉时长(分钟)')
    threshold = db.Column(db.Float, comment='湿度阈值(%)')
    status = db.Column(db.String(20), default='active', comment='状态: active/inactive')
    created_at = db.Column(db.DateTime, default=datetime.now)
    updated_at = db.Column(db.DateTime, default=datetime.now, onupdate=datetime.now)

    # 关联
    device = db.relationship('Device', backref='irrigation_plans')

    def to_dict(self):
        return {
            'id': self.id,
            'name': self.name,
            'deviceId': self.device_id,
            'deviceName': self.device.name if self.device else None,
            'mode': self.mode,
            'scheduleTime': self.schedule_time.strftime('%H:%M') if self.schedule_time else None,
            'duration': self.duration,
            'threshold': self.threshold,
            'status': self.status,
            'createTime': self.created_at.strftime('%Y-%m-%d %H:%M:%S')
        }


class IrrigationHistory(db.Model):
    __tablename__ = 'irrigation_history'

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    device_id = db.Column(db.Integer, db.ForeignKey('devices.id'), nullable=False)
    plan_id = db.Column(db.Integer, db.ForeignKey('irrigation_plans.id'), nullable=True)
    type = db.Column(db.String(20), nullable=False, comment='类型: manual/auto/scheduled')
    start_time = db.Column(db.DateTime, nullable=False, comment='开始时间')
    end_time = db.Column(db.DateTime, comment='结束时间')
    duration = db.Column(db.Integer, comment='实际时长(分钟)')
    water_used = db.Column(db.Float, comment='用水量(L)')
    status = db.Column(db.String(20), default='in_progress', comment='状态: in_progress/completed')
    created_at = db.Column(db.DateTime, default=datetime.now)

    # 关联
    device = db.relationship('Device', backref='irrigation_history')

    def to_dict(self):
        return {
            'id': self.id,
            'deviceId': self.device_id,
            'deviceName': self.device.name if self.device else None,
            'planId': self.plan_id,
            'type': self.type,
            'startTime': self.start_time.strftime('%Y-%m-%d %H:%M:%S'),
            'endTime': self.end_time.strftime('%Y-%m-%d %H:%M:%S') if self.end_time else None,
            'duration': self.duration,
            'waterUsed': self.water_used,
            'status': self.status
        }
