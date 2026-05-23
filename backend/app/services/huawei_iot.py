import requests
import json
import hmac
import hashlib
import base64
from datetime import datetime
from app.config import Config

class HuaweiIoTDA:
    """华为云 IoTDA 平台服务"""

    def __init__(self):
        self.endpoint = Config.HUAWEI_IOT_ENDPOINT
        self.project_id = Config.HUAWEI_IOT_PROJECT_ID
        self.access_key = Config.HUAWEI_IOT_ACCESS_KEY
        self.secret_key = Config.HUAWEI_IOT_SECRET_KEY
        self.product_id = Config.HUAWEI_IOT_PRODUCT_ID
        self.region = Config.HUAWEI_IOT_REGION
        self.token = None

    def _get_auth_headers(self):
        """获取认证请求头"""
        if not self.token:
            self._refresh_token()

        return {
            'Content-Type': 'application/json',
            'X-Auth-Token': self.token
        }

    def _refresh_token(self):
        """刷新认证 Token"""
        url = f'{self.endpoint}/v3/auth/tokens'
        body = {
            'auth': {
                'identity': {
                    'methods': ['hw_ak_sk'],
                    'hw_ak_sk': {
                        'access': {
                            'key': self.access_key
                        },
                        'secret': {
                            'key': self.secret_key
                        }
                    }
                },
                'scope': {
                    'project': {
                        'name': self.region
                    }
                }
            }
        }

        try:
            response = requests.post(url, json=body)
            if response.status_code == 201:
                self.token = response.headers.get('X-Subject-Token')
                return True
            else:
                print(f'获取 Token 失败: {response.status_code} - {response.text}')
                return False
        except Exception as e:
            print(f'获取 Token 异常: {e}')
            return False

    def register_device(self, device_id, node_id, name, description=''):
        """注册设备到华为云 IoTDA"""
        url = f'{self.endpoint}/v5/iot/{self.project_id}/devices'
        body = {
            'device_id': device_id,
            'node_id': node_id,
            'product_id': self.product_id,
            'device_name': name,
            'description': description,
            'timeout': 0
        }

        try:
            response = requests.post(
                url,
                json=body,
                headers=self._get_auth_headers()
            )

            if response.status_code == 201:
                result = response.json()
                return {
                    'success': True,
                    'device_id': result.get('device_id'),
                    'secret': result.get('secret')
                }
            else:
                return {
                    'success': False,
                    'error': response.text
                }
        except Exception as e:
            return {
                'success': False,
                'error': str(e)
            }

    def delete_device(self, device_id):
        """从华为云 IoTDA 删除设备"""
        url = f'{self.endpoint}/v5/iot/{self.project_id}/devices/{device_id}'

        try:
            response = requests.delete(
                url,
                headers=self._get_auth_headers()
            )

            return response.status_code == 204
        except Exception as e:
            print(f'删除设备异常: {e}')
            return False

    def get_device_info(self, device_id):
        """获取设备信息"""
        url = f'{self.endpoint}/v5/iot/{self.project_id}/devices/{device_id}'

        try:
            response = requests.get(
                url,
                headers=self._get_auth_headers()
            )

            if response.status_code == 200:
                return response.json()
            return None
        except Exception as e:
            print(f'获取设备信息异常: {e}')
            return None

    def get_device_shadow(self, device_id):
        """获取设备影子数据"""
        url = f'{self.endpoint}/v5/iot/{self.project_id}/devices/{device_id}/shadow'

        try:
            response = requests.get(
                url,
                headers=self._get_auth_headers()
            )

            if response.status_code == 200:
                return response.json()
            return None
        except Exception as e:
            print(f'获取设备影子异常: {e}')
            return None

    def send_command(self, device_id, service_id, command_name, paras):
        """下发设备命令"""
        url = f'{self.endpoint}/v5/iot/{self.project_id}/devices/{device_id}/commands'
        body = {
            'service_id': service_id,
            'command_name': command_name,
            'paras': paras
        }

        try:
            response = requests.post(
                url,
                json=body,
                headers=self._get_auth_headers()
            )

            if response.status_code == 200:
                return {
                    'success': True,
                    'command_id': response.json().get('command_id')
                }
            else:
                return {
                    'success': False,
                    'error': response.text
                }
        except Exception as e:
            return {
                'success': False,
                'error': str(e)
            }

    def get_device_messages(self, device_id, limit=10):
        """获取设备消息列表"""
        url = f'{self.endpoint}/v5/iot/{self.project_id}/devices/{device_id}/messages'
        params = {'limit': limit}

        try:
            response = requests.get(
                url,
                params=params,
                headers=self._get_auth_headers()
            )

            if response.status_code == 200:
                return response.json().get('messages', [])
            return []
        except Exception as e:
            print(f'获取设备消息异常: {e}')
            return []

    def query_device_data(self, device_id, service_id, property, start_time, end_time, limit=50):
        """查询设备数据"""
        url = f'{self.endpoint}/v5/iot/{self.project_id}/datas'
        params = {
            'device_id': device_id,
            'service_id': service_id,
            'property': property,
            'start_time': start_time,
            'end_time': end_time,
            'limit': limit
        }

        try:
            response = requests.get(
                url,
                params=params,
                headers=self._get_auth_headers()
            )

            if response.status_code == 200:
                return response.json().get('records', [])
            return []
        except Exception as e:
            print(f'查询设备数据异常: {e}')
            return []

    def create_amqp_queue(self, queue_name):
        """创建 AMQP 队列用于接收设备消息"""
        url = f'{self.endpoint}/v5/iot/{self.project_id}/amqp-queues'
        body = {
            'queue_name': queue_name
        }

        try:
            response = requests.post(
                url,
                json=body,
                headers=self._get_auth_headers()
            )

            if response.status_code == 201:
                return response.json()
            return None
        except Exception as e:
            print(f'创建 AMQP 队列异常: {e}')
            return None


# 单例实例
huawei_iot = HuaweiIoTDA()
