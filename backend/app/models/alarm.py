from app import db
from datetime import datetime

class Alarm(db.Model):
    __tablename__ = 'alarms'

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    device_id = db.Column(db.Integer, db.ForeignKey('devices.id'), nullable=False)
    level = db.Column(db.String(20), nullable=False, comment='级别: critical/warning/info')
    type = db.Column(db.String(50), nullable=False, comment='类型: humidity/temperature/device/communication')
    message = db.Column(db.String(500), nullable=False, comment='报警信息')
    value = db.Column(db.String(50), comment='当前值')
    threshold = db.Column(db.String(50), comment='阈值')
    status = db.Column(db.String(20), default='unhandled', comment='状态: unhandled/handled')
    handle_time = db.Column(db.DateTime, comment='处理时间')
    handler = db.Column(db.String(50), comment='处理人')
    handle_remark = db.Column(db.Text, comment='处理说明')
    created_at = db.Column(db.DateTime, default=datetime.now)

    # 关联
    device = db.relationship('Device', backref='alarms')

    def to_dict(self):
        return {
            'id': self.id,
            'deviceId': self.device_id,
            'deviceName': self.device.name if self.device else None,
            'level': self.level,
            'type': self.type,
            'message': self.message,
            'value': self.value,
            'threshold': self.threshold,
            'status': self.status,
            'handleTime': self.handle_time.strftime('%Y-%m-%d %H:%M:%S') if self.handle_time else None,
            'handler': self.handler,
            'handleRemark': self.handle_remark,
            'time': self.created_at.strftime('%Y-%m-%d %H:%M:%S')
        }
