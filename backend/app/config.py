import os
from dotenv import load_dotenv

load_dotenv(os.path.join(os.path.dirname(__file__), '..', '.env'))

class Config:
    # 数据库配置
    MYSQL_HOST = os.getenv('MYSQL_HOST', 'localhost')
    MYSQL_PORT = int(os.getenv('MYSQL_PORT', 3306))
    MYSQL_USER = os.getenv('MYSQL_USER', 'root')
    MYSQL_PASSWORD = os.getenv('MYSQL_PASSWORD', '')
    MYSQL_DB = os.getenv('MYSQL_DB', 'irrigation')

    DATABASE_URL = os.getenv('DATABASE_URL', '')

    @classmethod
    def get_database_uri(cls):
        if cls.DATABASE_URL:
            return cls.DATABASE_URL
        if cls.MYSQL_PASSWORD:
            return f"mysql+pymysql://{cls.MYSQL_USER}:{cls.MYSQL_PASSWORD}@{cls.MYSQL_HOST}:{cls.MYSQL_PORT}/{cls.MYSQL_DB}"
        import os as _os
        basedir = _os.path.abspath(_os.path.dirname(__file__))
        return f"sqlite:///{_os.path.join(basedir, '..', 'irrigation.db')}"

    SQLALCHEMY_TRACK_MODIFICATIONS = False

    # MQTT 配置
    MQTT_BROKER = os.getenv('MQTT_BROKER', 'localhost')
    MQTT_PORT = int(os.getenv('MQTT_PORT', 1883))
    MQTT_USERNAME = os.getenv('MQTT_USERNAME', '')
    MQTT_PASSWORD = os.getenv('MQTT_PASSWORD', '')

    # 华为云 IoTDA 配置
    HUAWEI_IOT_ENDPOINT = os.getenv('HUAWEI_IOT_ENDPOINT', '')
    HUAWEI_IOT_PROJECT_ID = os.getenv('HUAWEI_IOT_PROJECT_ID', '')
    HUAWEI_IOT_ACCESS_KEY = os.getenv('HUAWEI_IOT_ACCESS_KEY', '')
    HUAWEI_IOT_SECRET_KEY = os.getenv('HUAWEI_IOT_SECRET_KEY', '')
    HUAWEI_IOT_PRODUCT_ID = os.getenv('HUAWEI_IOT_PRODUCT_ID', '')
    HUAWEI_IOT_DEVICE_ID = os.getenv('HUAWEI_IOT_DEVICE_ID', '')
    HUAWEI_IOT_REGION = os.getenv('HUAWEI_IOT_REGION', 'cn-north-4')
