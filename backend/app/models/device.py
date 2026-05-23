from app import db
from datetime import datetime

class Device(db.Model):
    __tablename__ = 'devices'

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    device_id = db.Column(db.String(50), unique=True, nullable=False, comment='设备ID')
    name = db.Column(db.String(100), nullable=False, comment='设备名称')
    type = db.Column(db.String(50), nullable=False, comment='设备类型')
    location = db.Column(db.String(200), comment='安装位置')
    status = db.Column(db.String(20), default='offline', comment='设备状态')
    battery = db.Column(db.Integer, default=100, comment='电量')
    last_online = db.Column(db.DateTime, comment='最后在线时间')
    huawei_device_id = db.Column(db.String(100), comment='华为云设备ID')
    remark = db.Column(db.Text, comment='备注')
    created_at = db.Column(db.DateTime, default=datetime.now)
    updated_at = db.Column(db.DateTime, default=datetime.now, onupdate=datetime.now)

    # 关联
    sensor_data = db.relationship('SensorData', backref='device', lazy='dynamic')

    def to_dict(self):
        return {
            'id': self.id,
            'deviceId': self.device_id,
            'name': self.name,
            'type': self.type,
            'location': self.location,
            'status': self.status,
            'battery': self.battery,
            'lastOnline': self.last_online.strftime('%Y-%m-%d %H:%M:%S') if self.last_online else None,
            'huaweiDeviceId': self.huawei_device_id,
            'remark': self.remark,
            'createTime': self.created_at.strftime('%Y-%m-%d %H:%M:%S'),
            'updateTime': self.updated_at.strftime('%Y-%m-%d %H:%M:%S')
        }
