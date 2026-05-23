from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_cors import CORS
from dotenv import load_dotenv

db = SQLAlchemy()

def create_app():
    load_dotenv()

    app = Flask(__name__)

    from app.config import Config
    app.config['SQLALCHEMY_DATABASE_URI'] = Config.get_database_uri()
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

    # 初始化扩展
    db.init_app(app)
    CORS(app)

    # 注册路由
    from app.routes.device import device_bp
    from app.routes.data import data_bp
    from app.routes.irrigation import irrigation_bp
    from app.routes.alarm import alarm_bp

    app.register_blueprint(device_bp, url_prefix='/api/devices')
    app.register_blueprint(data_bp, url_prefix='/api/data')
    app.register_blueprint(irrigation_bp, url_prefix='/api/irrigation')
    app.register_blueprint(alarm_bp, url_prefix='/api/alarms')

    # 创建数据库表
    with app.app_context():
        db.create_all()

    return app
