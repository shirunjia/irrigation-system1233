import os
from app import create_app
from app.services.mqtt_service import start_mqtt
from app.services.rule_engine import start_rule_engine

app = create_app()

if __name__ == '__main__':
    # 启动 MQTT 服务
    start_mqtt(app)

    # 启动规则引擎
    start_rule_engine(app)

    # 启动 Flask 应用
    port = int(os.getenv('FLASK_PORT', 5000))
    debug = os.getenv('FLASK_DEBUG', 'true').lower() == 'true'
    app.run(host='0.0.0.0', port=port, debug=debug)
