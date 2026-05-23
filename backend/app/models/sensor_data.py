from app import db
from datetime import datetime

class SensorData(db.Model):
    __tablename__ = 'sensor_data'

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    device_id = db.Column(db.Integer, db.ForeignKey('devices.id'), nullable=False)
    soil_moisture = db.Column(db.Float, comment='土壤湿度(%)')
    temperature = db.Column(db.Float, comment='温度(°C)')
    humidity = db.Column(db.Float, comment='空气湿度(%)')
    light_intensity = db.Column(db.Float, comment='光照强度(lux)')
    soil_temperature = db.Column(db.Float, comment='土壤温度(°C)')
    timestamp = db.Column(db.DateTime, default=datetime.now, comment='采集时间')
    raw_data = db.Column(db.JSON, comment='原始数据')

    def to_dict(self):
        return {
            'id': self.id,
            'deviceId': self.device_id,
            'soilMoisture': self.soil_moisture,
            'temperature': self.temperature,
            'humidity': self.humidity,
            'lightIntensity': self.light_intensity,
            'soilTemperature': self.soil_temperature,
            'timestamp': self.timestamp.strftime('%Y-%m-%d %H:%M:%S'),
            'rawData': self.raw_data
        }
