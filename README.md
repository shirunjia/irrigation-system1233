# 智能灌溉系统

全栈 IoT 智能灌溉管理系统，实时监测田间传感器数据，支持自动规则、定时计划和手动控制三种灌溉方式。集成华为云 IoTDA 平台进行设备通信，使用 MQTT 协议实现实时消息传输。

## 功能特性

- **实时监控** -- 采集土壤湿度、空气温度、空气湿度、光照强度、土壤温度等传感器数据，覆盖多个农业区域
- **自动灌溉** -- 规则引擎每分钟检测土壤湿度，低于设定阈值时自动触发灌溉
- **定时灌溉** -- 支持按时间计划执行灌溉（如每天 06:00）
- **手动灌溉** -- 运营人员可通过仪表盘按需启动/停止灌溉，指定设备和时长
- **告警管理** -- 传感器数据超阈值时自动生成告警（湿度不足、温度过高、设备离线、通信异常），支持严重等级分类（紧急/警告/提示）和批量处理
- **设备管理** -- 传感器和阀门的增删改查，自动在华为云 IoTDA 平台注册/注销设备
- **数据可视化** -- 基于 ECharts 的湿度分布、温度分布、设备状态、告警趋势等图表展示

## 技术栈

### 后端

| 组件 | 技术 |
|---|---|
| Web 框架 | Flask 3.0.0 |
| ORM | Flask-SQLAlchemy 3.1.1 |
| 数据库 | SQLite（开发）/ MySQL（生产） |
| 跨域 | Flask-CORS 4.0.0 |
| 消息通信 | Paho MQTT 1.6.1 |
| 任务调度 | APScheduler 3.10.4 |
| 云平台 | 华为云 IoTDA |

### 前端

| 组件 | 技术 |
|---|---|
| 框架 | Vue 3.3.4（Composition API） |
| 路由 | Vue Router 4.2.4 |
| 构建工具 | Vite 4.4.9 |
| UI 组件库 | Element Plus 2.3.14 |
| 状态管理 | Pinia 2.1.4 |
| 图表库 | ECharts 5.4.3 |

## 项目结构

```
irrigation-system/
├── backend/
│   ├── .env.example            # 环境变量示例（复制为 .env 后填写）
│   ├── requirements.txt        # Python 依赖
│   ├── run.py                  # 应用启动入口
│   ├── seed_data.py            # 演示数据填充脚本
│   └── app/
│       ├── __init__.py         # Flask 应用工厂
│       ├── config.py           # 配置类
│       ├── models/             # 数据模型（设备、传感器数据、灌溉、告警）
│       ├── services/           # MQTT 服务、规则引擎、华为云 IoTDA 客户端
│       └── routes/             # REST API 路由
├── database/
│   └── init.sql                # MySQL 建表语句 + 示例数据
└── frontend/
    ├── .env.local.example      # 前端环境变量示例
    ├── package.json
    ├── vite.config.js
    └── src/
        ├── App.vue             # 根布局（侧边栏 + 顶栏 + 路由视图）
        ├── router/             # Vue Router 路由配置
        ├── api/                # Axios API 封装
        ├── stores/             # Pinia 状态管理
        └── views/              # 页面：仪表盘、设备管理、灌溉设置、报警信息
```

## 快速开始

### 环境要求

- Python 3.10+
- Node.js 16+ 和 npm
-（生产环境可选）MySQL 5.7+

### 后端启动

```bash
cd backend

# 安装依赖
pip install -r requirements.txt

# 配置环境变量
# 编辑 .env 文件，设置数据库、MQTT 和华为云 IoTDA 凭据

# 填充演示数据（可选）
python seed_data.py

# 启动后端服务
python run.py
```

后端启动后同时运行三个服务：
- Flask HTTP 服务，监听 `0.0.0.0:5000`
- MQTT 客户端，订阅设备数据/状态主题
- 规则引擎，后台定时任务调度

### 前端启动

```bash
cd frontend

# 安装依赖
npm install

# 启动开发服务器
npm run dev

# 生产环境构建
npm run build
```

前端开发服务器运行在 `http://localhost:3000`，通过 Vite 代理将 `/api/*` 请求转发到 Flask 后端 `http://localhost:5000`。

### 访问应用

在浏览器中打开 `http://localhost:3000`。

## 环境变量

### 后端

复制 `backend/.env.example` 为 `backend/.env` 并填写实际配置：

| 变量名 | 默认值 | 说明 |
|---|---|---|
| `MYSQL_HOST` | localhost | MySQL 主机地址 |
| `MYSQL_PORT` | 3306 | MySQL 端口 |
| `MYSQL_USER` | root | MySQL 用户名 |
| `MYSQL_PASSWORD` | - | MySQL 密码 |
| `MYSQL_DB` | irrigation | MySQL 数据库名 |
| `DATABASE_URL` | - | 数据库连接串（设置后优先使用此配置） |
| `MQTT_BROKER` | localhost | MQTT Broker 地址 |
| `MQTT_PORT` | 1883 | MQTT Broker 端口 |
| `MQTT_USERNAME` | - | MQTT 认证用户名 |
| `MQTT_PASSWORD` | - | MQTT 认证密码 |
| `HUAWEI_IOT_ENDPOINT` | - | 华为云 IoTDA REST 端点 |
| `HUAWEI_IOT_PROJECT_ID` | - | 华为云项目 ID |
| `HUAWEI_IOT_ACCESS_KEY` | - | 华为云 IAM 访问密钥 |
| `HUAWEI_IOT_SECRET_KEY` | - | 华为云 IAM 密钥 |
| `HUAWEI_IOT_PRODUCT_ID` | - | 华为云 IoTDA 产品 ID |
| `HUAWEI_IOT_DEVICE_ID` | - | 华为云 IoTDA 设备 ID |
| `HUAWEI_IOT_DEVICE_SECRET` | - | 华为云 IoTDA 设备密钥 |
| `HUAWEI_IOT_REGION` | cn-north-4 | 华为云区域 |
| `HUAWEI_MQTT_BROKER` | - | 华为云 MQTT Broker 地址 |
| `HUAWEI_MQTT_PORT` | 1883 | 华为云 MQTT 端口 |
| `FLASK_DEBUG` | true | Flask 调试模式 |
| `FLASK_PORT` | 5000 | Flask 服务端口 |

> 若未设置 `DATABASE_URL`，系统默认使用 SQLite（`backend/irrigation.db`）。生产环境请设置 `DATABASE_URL` 为 MySQL 连接串，或配置 `MYSQL_*` 系列变量。

### 前端

复制 `frontend/.env.local.example` 为 `frontend/.env.local` 并按需配置：

| 变量名 | 默认值 | 说明 |
|---|---|---|
| `VITE_API_BASE_URL` | /api | 后端 API 地址，开发环境留空使用 Vite 代理，生产环境设置为实际后端地址 |

生产环境构建示例：
```bash
# 设置后端地址后构建
VITE_API_BASE_URL=http://your-server:5000/api npm run build
```

## API 接口

### 设备管理 `/api/devices`

| 方法 | 路径 | 说明 |
|---|---|---|
| GET | `/` | 设备列表（支持分页、关键字搜索、状态/类型筛选） |
| GET | `/<id>` | 获取设备详情 |
| POST | `/` | 创建设备（自动注册到华为云 IoTDA） |
| PUT | `/<id>` | 更新设备 |
| DELETE | `/<id>` | 删除设备（自动从华为云 IoTDA 注销） |
| POST | `/<id>/command` | 向设备发送 MQTT 指令 |
| GET | `/<device_id>/properties` | 获取设备最新传感器数据 |

### 传感器数据 `/api/data`

| 方法 | 路径 | 说明 |
|---|---|---|
| GET | `/<device_id>/latest` | 最新传感器读数 |
| GET | `/<device_id>/history` | 历史数据（支持时间范围、分页） |
| GET | `/stats` | 汇总统计信息 |
| GET | `/moisture-trend` | 湿度趋势（按天/周/月聚合） |

### 灌溉管理 `/api/irrigation`

| 方法 | 路径 | 说明 |
|---|---|---|
| GET | `/plans` | 灌溉计划列表 |
| POST | `/plans` | 创建灌溉计划 |
| PUT | `/plans/<id>` | 更新灌溉计划 |
| DELETE | `/plans/<id>` | 删除灌溉计划 |
| POST | `/control/<device_id>` | 手动灌溉开关 |
| GET | `/history` | 灌溉历史记录 |
| GET | `/stats` | 灌溉统计信息 |

### 告警管理 `/api/alarms`

| 方法 | 路径 | 说明 |
|---|---|---|
| GET | `/` | 告警列表（支持按等级、状态、类型、日期范围筛选） |
| GET | `/<id>` | 告警详情 |
| PUT | `/<id>/handle` | 处理告警 |
| GET | `/stats` | 告警统计信息 |
| POST | `/batch-handle` | 批量处理告警 |

## 后台服务

- **MQTT 服务** -- 订阅 `irrigation/devices/+/data` 和 `irrigation/devices/+/status` 主题，保存传感器数据，检查告警阈值（土壤湿度 < 20% 紧急告警、< 30% 警告；温度 > 35C 警告）
- **规则引擎** -- 每分钟检查自动灌溉计划（湿度低于阈值时触发）、定时灌溉计划执行，设备离线超 5 分钟自动标记为离线状态
- **华为云 IoTDA 客户端** -- 通过华为云 REST API 处理设备注册、设备影子数据、指令下发等操作

## 部署

### 生产环境构建

```bash
# 1. 后端部署
cd backend
pip install -r requirements.txt
cp .env.example .env  # 编辑 .env 填写实际配置
python run.py

# 2. 前端构建
cd frontend
npm install
VITE_API_BASE_URL=http://your-backend-server:5000/api npm run build
# 构建产物在 frontend/dist/ 目录，用 Nginx 等 Web 服务器托管
```

### Nginx 配置示例

```nginx
server {
    listen 80;
    server_name your-domain.com;

    # 前端静态文件
    location / {
        root /path/to/frontend/dist;
        try_files $uri $uri/ /index.html;
    }

    # API 反向代理
    location /api/ {
        proxy_pass http://localhost:5000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }
}
```

> 使用 Nginx 反向代理时，前端无需设置 `VITE_API_BASE_URL`，保持默认的 `/api` 即可。

## 许可证

MIT
