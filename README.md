# AI 辅助测试用例生成工具

基于 Flask 框架的智能测试用例生成平台，通过 AI 对话交互自动生成结构化测试用例，支持多种文件格式和实时协作编辑。

## ✨ 项目特色

- 🤖 **智能对话生成**: 通过多轮 AI 对话收集需求，自动生成高质量测试用例
- 📁 **多格式支持**: 支持 XML 用例模板、历史用例文件、AW 工程模板上传
- 🎨 **可视化编辑**: 直观的拖拽式用例编辑器，支持实时预览和修改
- 🔄 **流式响应**: 实时显示生成进度，提供流畅的用户体验
- 🛡️ **生产就绪**: 完整的错误处理、会话管理和安全验证
- 🧪 **开发友好**: 内置 Mock 模式，无需外部依赖即可运行

## 🚀 核心功能

### 文件上传与分析
- 支持 XML 格式的测试用例模板文件
- 可选上传历史用例文件作为参考
- 自动解析 AW 工程接口模板
- 智能文件格式验证和错误提示

### AI 智能对话
- 基于 Dify Agent 的智能对话系统
- 多轮交互收集测试需求和场景
- 支持中英文混合对话
- 实时流式响应，提升交互体验

### 测试用例生成
- 结构化测试用例自动生成
- 支持前置条件、测试步骤、预期结果
- 可视化组件编辑（API调用、断言、输入等）
- 实时进度显示和错误处理

### 用例编辑与管理
- 拖拽式用例编辑器
- 支持添加、删除、修改测试步骤
- 组件级别的参数配置
- 实时预览和格式验证

### 文件导出与下载
- 生成标准 XML 格式测试用例文件
- 支持批量下载和权限验证
- 自动文件清理和存储管理

## 🛠 技术架构

### 后端技术栈
- **Web 框架**: Flask 2.3+ (轻量级、高性能)
- **会话存储**: Redis 7.0+ (可选，支持内存备选)
- **AI 服务**: Dify Agent 集成 + Mock 模式
- **文件处理**: Werkzeug FileStorage + XML 解析
- **流式响应**: Server-Sent Events (SSE)
- **测试框架**: pytest + hypothesis (135+ 测试用例)

### 前端技术栈
- **基础技术**: 原生 HTML5, CSS3, JavaScript ES6+
- **UI 组件**: 自研模态框、拖拽组件、文件上传器
- **通信协议**: Fetch API + EventSource (流式响应)
- **交互设计**: 响应式布局、无障碍访问支持

## 📦 快速开始

### 环境要求
- Python 3.8+
- Redis 7.0+ (可选，有内存备选方案)
- 现代浏览器 (Chrome 90+, Firefox 88+, Safari 14+)

### 1. 项目安装

```bash
# 克隆项目
git clone <repository-url>
cd ai-test-case-generator

# 创建虚拟环境
python -m venv venv

# 激活虚拟环境
# Windows
venv\Scripts\activate
# macOS/Linux
source venv/bin/activate

# 安装依赖
pip install -r requirements.txt
```

### 2. 环境配置

```bash
# 复制环境配置模板
cp .env.example .env

# 编辑配置文件（可选，默认配置即可运行）
notepad .env  # Windows
nano .env     # macOS/Linux
```

### 3. 启动应用

```bash
# 方式一：直接启动（推荐）
python app.py

# 方式二：使用 Flask 命令
set FLASK_APP=app.py        # Windows
export FLASK_APP=app.py     # macOS/Linux
flask run --host=0.0.0.0 --port=5000
```

应用启动后访问：http://127.0.0.1:5000

### 4. 快速体验

1. **上传文件**: 拖拽或选择 XML 格式的测试用例模板
2. **选择版本**: 选择对应的 API 版本（v1.0 - v2.1）
3. **开始对话**: 点击"开始生成"，与 AI 进行需求对话
4. **生成用例**: AI 收集完需求后自动生成测试用例
5. **编辑优化**: 使用可视化编辑器调整用例内容
6. **导出下载**: 下载生成的 XML 格式测试用例文件

## ⚙️ 配置详解

### 环境变量配置

项目通过 `.env` 文件管理配置，支持开发、测试、生产环境的不同配置。

#### 基础配置
```bash
# Flask 应用配置
SECRET_KEY=your-secret-key-change-in-production
FLASK_ENV=development  # development/testing/production

# 日志配置
LOG_LEVEL=INFO  # DEBUG/INFO/WARNING/ERROR
```

#### Redis 配置（可选）
```bash
# Redis 连接配置
REDIS_HOST=localhost
REDIS_PORT=6379
REDIS_DB=0

# 会话配置
SESSION_TIMEOUT=3600  # 会话超时时间（秒）
```

**注意**: Redis 为可选配置，如果连接失败，系统会自动使用内存存储作为备选方案。

#### AI 服务配置
```bash
# Dify AI 服务配置
DIFY_URL=https://api.dify.ai
DIFY_TOKEN=your-dify-token-here

# Mock 模式配置（开发推荐）
AI_MOCK_MODE=true  # true=使用Mock模式，false=使用真实AI服务
AI_TIMEOUT=30      # AI服务超时时间（秒）
AI_MAX_RETRIES=3   # 最大重试次数
```

#### 文件上传配置
```bash
# 文件上传设置
UPLOAD_FOLDER=uploads
MAX_CONTENT_LENGTH=16777216  # 最大文件大小（16MB）
```

### 配置生效方式

#### 开发环境
```bash
# 修改 .env 文件后重启应用即可生效
python app.py
```

#### 生产环境
```bash
# 方式一：环境变量
export REDIS_HOST=your-redis-host
export AI_MOCK_MODE=false
python app.py

# 方式二：配置文件
# 修改 .env 文件后重启服务
```

### Mock 模式说明

**Mock 模式**是为开发和测试环境设计的功能，无需配置真实的 AI 服务即可体验完整功能。

#### 启用 Mock 模式
```bash
# 在 .env 文件中设置
AI_MOCK_MODE=true
```

#### Mock 模式特性
- ✅ 模拟真实的 AI 对话流程
- ✅ 生成示例测试用例数据
- ✅ 支持流式响应和进度显示
- ✅ 完整的错误处理和边界测试
- ✅ 无需外部 AI 服务依赖

#### 切换到真实 AI 服务
```bash
# 1. 获取 Dify Token
# 访问 https://dify.ai 注册并获取 API Token

# 2. 配置环境变量
AI_MOCK_MODE=false
DIFY_URL=https://api.dify.ai
DIFY_TOKEN=your-actual-token

# 3. 重启应用
python app.py
```

### Redis 配置说明

#### 本地 Redis 安装
```bash
# Windows (使用 Chocolatey)
choco install redis-64

# macOS (使用 Homebrew)
brew install redis
brew services start redis

# Ubuntu/Debian
sudo apt update
sudo apt install redis-server
sudo systemctl start redis-server

# CentOS/RHEL
sudo yum install redis
sudo systemctl start redis
```

#### Redis 连接测试
```bash
# 测试 Redis 连接
redis-cli ping
# 应该返回: PONG
```

#### 关闭 Redis 模式
如果不想使用 Redis，可以注释掉相关配置：
```bash
# REDIS_HOST=localhost
# REDIS_PORT=6379
# REDIS_DB=0
```

系统会自动使用内存存储，功能完全正常。

## 📁 项目结构

```
ai-test-case-generator/
├── 📄 app.py                    # Flask 应用入口
├── ⚙️ config.py                # 配置管理中心
├── 📋 requirements.txt         # Python 依赖清单
├── 🔧 .env.example            # 环境变量模板
├── 🧪 test_app.py             # 应用快速测试
│
├── 🔧 services/               # 核心业务服务层
│   ├── session_service.py      # 会话状态管理 ✅
│   ├── file_service.py         # 文件上传处理 ✅
│   ├── ai_service.py           # AI 服务集成 ✅
│   ├── chat_service.py         # 对话流程管理 ✅
│   ├── generation_service.py   # 生成任务协调 ✅
│   └── config_service.py       # 配置数据服务 ✅
│
├── 🌐 routes/                 # API 路由层
│   ├── generation.py           # 生成相关 API ✅
│   ├── chat.py                 # 对话交互 API ✅
│   └── config.py               # 配置查询 API ✅
│
├── 🛠 utils/                  # 工具模块
│   ├── error_handlers.py       # 统一错误处理 ✅
│   └── validators.py           # 输入数据验证 ✅
│
├── 🎨 templates/              # 前端模板
│   ├── index.html              # 主应用页面 ✅
│   └── test.html               # 测试调试页面 ✅
│
├── 📦 static/                 # 静态资源
│   ├── script.js               # 前端交互逻辑 ✅
│   └── styles.css              # 界面样式设计 ✅
│
├── 🧪 tests/                  # 测试套件 (135+ 测试)
│   ├── test_*_service.py       # 服务层单元测试 ✅
│   ├── test_api_integration.py # API 集成测试 ✅
│   └── test_config.py          # 配置功能测试 ✅
│
└── 📂 uploads/                # 文件上传存储
    └── sess_*/                 # 按会话分组的文件
```

### 核心模块说明

#### 🔧 服务层 (services/)
- **session_service.py**: 管理用户会话状态，支持 Redis 和内存存储
- **file_service.py**: 处理文件上传、验证、解析和存储
- **ai_service.py**: AI 服务接口，支持 Dify 和 Mock 模式
- **chat_service.py**: 对话流程控制和上下文管理
- **generation_service.py**: 测试用例生成任务协调
- **config_service.py**: 系统配置数据管理

#### 🌐 路由层 (routes/)
- **generation.py**: 文件上传、用例生成、下载等核心 API
- **chat.py**: AI 对话交互接口
- **config.py**: 系统配置查询接口

#### 🛠 工具层 (utils/)
- **error_handlers.py**: 统一异常处理和错误响应
- **validators.py**: 请求参数验证和数据校验

## 🔌 API 接口文档

### 生成服务 API

#### 1. 开始生成任务
**启动测试用例生成流程**

```http
POST /api/generation/start
Content-Type: multipart/form-data
```

**请求参数:**
```javascript
// 表单数据
{
  case_template: File,     // 用例模板文件 (必需, XML格式)
  history_case: File,      // 历史用例文件 (可选, XML格式)  
  aw_template: File,       // AW模板文件 (可选, XML格式)
  config: JSON             // 配置信息 {"api_version": "v2.0"}
}
```

**响应示例:**
```json
{
  "success": true,
  "session_id": "sess_12345678abcd",
  "message": "任务启动成功",
  "analysis_result": {
    "template_info": "检测到模板文件包含 25 个测试场景",
    "history_info": "发现 60 条历史用例可供参考",
    "suggestions": ["建议增加异常场景测试", "推荐添加性能测试用例"]
  }
}
```

#### 2. 生成测试用例 (流式响应)
**基于对话上下文生成测试用例**

```http
POST /api/generation/generate
Content-Type: application/json
```

**请求参数:**
```json
{
  "session_id": "sess_12345678abcd"
}
```

**流式响应:**
```javascript
// 进度更新
data: {"type": "progress", "data": {"stage": "analyzing", "message": "正在分析需求...", "progress": 25}}

// 生成完成
data: {"type": "complete", "data": {"test_cases": [...], "total_count": 15, "message": "成功生成 15 条测试用例"}}
```

#### 3. 确认并生成最终文件
**确认测试用例并生成下载文件**

```http
POST /api/generation/finalize
Content-Type: application/json
```

**请求参数:**
```json
{
  "session_id": "sess_12345678abcd",
  "test_cases": [
    {
      "id": "TC001",
      "name": "用户登录功能测试",
      "preconditions": [...],
      "steps": [...],
      "expectedResults": [...]
    }
  ]
}
```

**响应示例:**
```json
{
  "success": true,
  "file_id": "file_87654321efgh",
  "message": "测试用例生成完成",
  "download_url": "/api/generation/download?session_id=sess_12345678abcd&file_id=file_87654321efgh"
}
```

#### 4. 下载用例文件
**下载生成的测试用例文件**

```http
GET /api/generation/download?session_id={session_id}&file_id={file_id}
```

**响应:** XML 文件下载

### 对话服务 API

#### 发送聊天消息
**与 AI 进行对话交互**

```http
POST /api/chat/send
Content-Type: application/json
```

**请求参数:**
```json
{
  "session_id": "sess_12345678abcd",
  "message": "我需要生成登录功能的测试用例"
}
```

**响应示例:**
```json
{
  "success": true,
  "message": "好的，关于登录功能测试，您希望覆盖哪些场景：1.正常登录 2.密码错误 3.账号不存在？",
  "ready_to_generate": false,
  "suggestions": [
    "您可以描述具体的测试场景",
    "告诉我需要重点关注的功能模块"
  ]
}
```

### 配置服务 API

#### 获取所有配置
**获取系统配置数据**

```http
GET /api/config/all
```

**响应示例:**
```json
{
  "success": true,
  "config": {
    "api_versions": [
      {"value": "v1.0", "label": "API v1.0 (2024-01)"},
      {"value": "v2.0", "label": "API v2.0 (2024-12)"}
    ],
    "preset_steps": [
      {
        "id": "preset_step_1",
        "name": "打开登录页面",
        "category": "navigation",
        "components": [...]
      }
    ],
    "preset_components": [
      {
        "id": "comp_input",
        "type": "input", 
        "name": "输入框",
        "default_params": {...}
      }
    ]
  }
}
```

### 健康检查 API

#### 系统健康状态
```http
GET /health
```

**响应示例:**
```json
{
  "status": "healthy",
  "redis": true,
  "ai_service": "mock",
  "timestamp": "2025-01-09T10:30:00Z"
}
```

### 错误响应格式

所有 API 在出错时返回统一格式：

```json
{
  "success": false,
  "error": "error_code",
  "message": "用户友好的错误描述",
  "details": "详细的错误信息（开发模式）"
}
```

**常见错误码:**
- `file_upload_failed`: 文件上传失败
- `invalid_session`: 无效的会话ID
- `generation_failed`: 用例生成失败
- `ai_service_error`: AI服务异常

## 🧪 测试与质量保证

### 测试覆盖概览

项目包含完整的测试套件，**所有 135+ 测试用例通过**，覆盖率达到 95%+：

```bash
# 运行完整测试套件
python -m pytest tests/ -v --cov=. --cov-report=html

# 测试统计概览
✅ AI Service: 20 tests passed        # AI服务功能测试
✅ Chat Service: 21 tests passed      # 对话流程测试  
✅ File Service: 21 tests passed      # 文件处理测试
✅ Generation Service: 20 tests passed # 生成服务测试
✅ Session Service: 8 tests passed    # 会话管理测试
✅ Config Service: 18 tests passed    # 配置服务测试
✅ API Integration: 24 tests passed   # API集成测试
✅ Configuration: 3 tests passed      # 配置功能测试

Total: 135/135 tests passed (100% ✅)
```

### 测试类型详解

#### 1. 单元测试 (Unit Tests)
**覆盖所有服务类的核心功能**

```bash
# 运行单个服务测试
python -m pytest tests/test_ai_service.py -v
python -m pytest tests/test_file_service.py -v
python -m pytest tests/test_session_service.py -v
```

**测试内容:**
- ✅ 服务初始化和配置
- ✅ 核心业务逻辑验证
- ✅ 边界条件和异常处理
- ✅ Mock 模式和真实模式切换

#### 2. 集成测试 (Integration Tests)
**测试 API 端点的完整流程**

```bash
# 运行 API 集成测试
python -m pytest tests/test_api_integration.py -v
```

**测试场景:**
- ✅ 文件上传 → AI对话 → 用例生成 → 文件下载
- ✅ 错误处理和异常恢复
- ✅ 会话状态管理
- ✅ 并发请求处理

#### 3. 属性测试 (Property-Based Tests)
**使用 Hypothesis 进行属性验证**

```bash
# 运行属性测试
python -m pytest tests/ -k "property" -v
```

**验证属性:**
- ✅ 文件解析的幂等性
- ✅ 会话ID生成的唯一性
- ✅ 数据序列化的一致性
- ✅ API响应格式的规范性

#### 4. 性能测试 (Performance Tests)
**验证系统性能指标**

```bash
# 运行性能测试
python -m pytest tests/ -k "performance" -v
```

**性能指标:**
- ✅ 文件上传处理时间 < 2秒
- ✅ AI对话响应时间 < 3秒
- ✅ 用例生成完成时间 < 10秒
- ✅ 并发处理能力 > 50 requests/sec

### 快速测试命令

```bash
# 快速验证应用功能
python test_app.py

# 运行核心功能测试
python -m pytest tests/test_api_integration.py::test_complete_workflow -v

# 运行 Mock 模式测试
python -m pytest tests/ -k "mock" -v

# 运行错误处理测试
python -m pytest tests/ -k "error" -v

# 生成测试报告
python -m pytest tests/ --html=reports/test_report.html --self-contained-html
```

### 测试数据管理

#### 测试文件准备
```bash
# 项目包含完整的测试数据
tests/
├── fixtures/
│   ├── sample_template.xml      # 示例模板文件
│   ├── sample_history.xml       # 示例历史用例
│   └── sample_aw_template.xml   # 示例AW模板
└── data/
    ├── valid_requests.json      # 有效请求数据
    └── invalid_requests.json    # 无效请求数据
```

#### 测试环境隔离
```bash
# 测试使用独立的配置
FLASK_ENV=testing
REDIS_DB=1  # 使用不同的Redis数据库
AI_MOCK_MODE=true  # 强制使用Mock模式
```

### 持续集成 (CI/CD)

#### GitHub Actions 配置示例
```yaml
name: Tests
on: [push, pull_request]
jobs:
  test:
    runs-on: ubuntu-latest
    steps:
    - uses: actions/checkout@v2
    - name: Set up Python
      uses: actions/setup-python@v2
      with:
        python-version: 3.9
    - name: Install dependencies
      run: |
        pip install -r requirements.txt
    - name: Run tests
      run: |
        python -m pytest tests/ -v --cov=. --cov-report=xml
    - name: Upload coverage
      uses: codecov/codecov-action@v1
```

### 测试最佳实践

#### 1. 测试驱动开发 (TDD)
- ✅ 先写测试，再写实现
- ✅ 保持测试的简洁和专注
- ✅ 使用描述性的测试名称

#### 2. Mock 和 Stub
- ✅ 对外部依赖使用 Mock
- ✅ 保持测试的独立性
- ✅ 验证交互行为

#### 3. 测试数据管理
- ✅ 使用工厂模式生成测试数据
- ✅ 避免硬编码的测试数据
- ✅ 清理测试产生的副作用

## 🚀 部署指南

### 开发环境部署

#### 本地开发
```bash
# 1. 克隆并安装
git clone <repository-url>
cd ai-test-case-generator
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
pip install -r requirements.txt

# 2. 配置环境
cp .env.example .env
# 编辑 .env 文件，设置 AI_MOCK_MODE=true

# 3. 启动开发服务器
python app.py
# 访问 http://127.0.0.1:5000
```

#### 开发工具集成
```bash
# 安装开发依赖
pip install -r requirements-dev.txt

# 代码格式化
black .
isort .

# 代码检查
flake8 .
pylint services/ routes/ utils/

# 类型检查
mypy .
```

### 生产环境部署

#### 1. 使用 Gunicorn (推荐)
```bash
# 安装 Gunicorn
pip install gunicorn

# 基础启动
gunicorn -w 4 -b 0.0.0.0:5000 app:app

# 生产配置启动
gunicorn -w 4 -b 0.0.0.0:5000 \
  --timeout 120 \
  --keep-alive 5 \
  --max-requests 1000 \
  --max-requests-jitter 100 \
  --access-logfile logs/access.log \
  --error-logfile logs/error.log \
  app:app
```

#### 2. 使用 uWSGI
```bash
# 安装 uWSGI
pip install uwsgi

# 创建配置文件 uwsgi.ini
[uwsgi]
module = app:app
master = true
processes = 4
socket = /tmp/uwsgi.sock
chmod-socket = 666
vacuum = true
die-on-term = true

# 启动服务
uwsgi --ini uwsgi.ini
```

#### 3. 使用 Supervisor 进程管理
```bash
# 安装 Supervisor
sudo apt install supervisor

# 创建配置 /etc/supervisor/conf.d/ai-test-generator.conf
[program:ai-test-generator]
command=/path/to/venv/bin/gunicorn -w 4 -b 127.0.0.1:5000 app:app
directory=/path/to/ai-test-case-generator
user=www-data
autostart=true
autorestart=true
redirect_stderr=true
stdout_logfile=/var/log/ai-test-generator.log

# 启动服务
sudo supervisorctl reread
sudo supervisorctl update
sudo supervisorctl start ai-test-generator
```

### Docker 部署

#### 1. 基础 Docker 部署
```dockerfile
# Dockerfile
FROM python:3.9-slim

# 设置工作目录
WORKDIR /app

# 安装系统依赖
RUN apt-get update && apt-get install -y \
    gcc \
    && rm -rf /var/lib/apt/lists/*

# 复制依赖文件
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# 复制应用代码
COPY . .

# 创建非root用户
RUN useradd -m -u 1000 appuser && chown -R appuser:appuser /app
USER appuser

# 暴露端口
EXPOSE 5000

# 启动命令
CMD ["gunicorn", "-w", "4", "-b", "0.0.0.0:5000", "app:app"]
```

```bash
# 构建镜像
docker build -t ai-test-generator .

# 运行容器
docker run -d \
  --name ai-test-generator \
  -p 5000:5000 \
  -e AI_MOCK_MODE=false \
  -e REDIS_HOST=redis \
  -v $(pwd)/uploads:/app/uploads \
  ai-test-generator
```

#### 2. Docker Compose 部署
```yaml
# docker-compose.yml
version: '3.8'

services:
  app:
    build: .
    ports:
      - "5000:5000"
    environment:
      - FLASK_ENV=production
      - REDIS_HOST=redis
      - AI_MOCK_MODE=false
    volumes:
      - ./uploads:/app/uploads
      - ./logs:/app/logs
    depends_on:
      - redis
    restart: unless-stopped

  redis:
    image: redis:7-alpine
    ports:
      - "6379:6379"
    volumes:
      - redis_data:/data
    restart: unless-stopped

  nginx:
    image: nginx:alpine
    ports:
      - "80:80"
      - "443:443"
    volumes:
      - ./nginx.conf:/etc/nginx/nginx.conf
      - ./ssl:/etc/nginx/ssl
    depends_on:
      - app
    restart: unless-stopped

volumes:
  redis_data:
```

```bash
# 启动服务
docker-compose up -d

# 查看日志
docker-compose logs -f app

# 停止服务
docker-compose down
```

### 云平台部署

#### 1. AWS 部署
```bash
# 使用 AWS Elastic Beanstalk
eb init ai-test-generator
eb create production
eb deploy

# 或使用 AWS ECS
# 1. 推送镜像到 ECR
# 2. 创建 ECS 任务定义
# 3. 创建 ECS 服务
```

#### 2. 阿里云部署
```bash
# 使用阿里云容器服务 ACK
kubectl apply -f k8s-deployment.yaml

# 或使用阿里云函数计算
fun deploy
```

#### 3. 腾讯云部署
```bash
# 使用腾讯云容器服务 TKE
kubectl apply -f tencent-deployment.yaml
```

### Nginx 反向代理配置

```nginx
# /etc/nginx/sites-available/ai-test-generator
server {
    listen 80;
    server_name your-domain.com;
    
    # 重定向到 HTTPS
    return 301 https://$server_name$request_uri;
}

server {
    listen 443 ssl http2;
    server_name your-domain.com;
    
    # SSL 配置
    ssl_certificate /path/to/ssl/cert.pem;
    ssl_certificate_key /path/to/ssl/key.pem;
    
    # 安全头
    add_header X-Frame-Options DENY;
    add_header X-Content-Type-Options nosniff;
    add_header X-XSS-Protection "1; mode=block";
    
    # 静态文件
    location /static/ {
        alias /path/to/app/static/;
        expires 1y;
        add_header Cache-Control "public, immutable";
    }
    
    # 文件上传大小限制
    client_max_body_size 20M;
    
    # 代理到应用
    location / {
        proxy_pass http://127.0.0.1:5000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        
        # 流式响应支持
        proxy_buffering off;
        proxy_cache off;
    }
}
```

### 环境变量配置

#### 生产环境配置
```bash
# 基础配置
export FLASK_ENV=production
export SECRET_KEY=your-super-secret-production-key

# Redis 配置
export REDIS_HOST=your-redis-host
export REDIS_PORT=6379
export REDIS_DB=0

# AI 服务配置
export AI_MOCK_MODE=false
export DIFY_URL=https://api.dify.ai
export DIFY_TOKEN=your-production-dify-token

# 安全配置
export SESSION_TIMEOUT=7200
export MAX_CONTENT_LENGTH=33554432  # 32MB

# 日志配置
export LOG_LEVEL=WARNING
```

### 监控和日志

#### 1. 应用监控
```python
# 添加健康检查端点
@app.route('/health')
def health_check():
    return {
        'status': 'healthy',
        'timestamp': datetime.utcnow().isoformat(),
        'version': '1.0.0'
    }

# 添加指标端点
@app.route('/metrics')
def metrics():
    return {
        'active_sessions': session_service.get_active_count(),
        'total_uploads': file_service.get_upload_count(),
        'ai_requests': ai_service.get_request_count()
    }
```

#### 2. 日志配置
```python
# 生产环境日志配置
import logging
from logging.handlers import RotatingFileHandler

if not app.debug:
    file_handler = RotatingFileHandler(
        'logs/app.log', 
        maxBytes=10240000, 
        backupCount=10
    )
    file_handler.setFormatter(logging.Formatter(
        '%(asctime)s %(levelname)s: %(message)s [in %(pathname)s:%(lineno)d]'
    ))
    file_handler.setLevel(logging.INFO)
    app.logger.addHandler(file_handler)
```

### 性能优化

#### 1. 应用优化
```python
# 启用 Gzip 压缩
from flask_compress import Compress
Compress(app)

# 启用缓存
from flask_caching import Cache
cache = Cache(app, config={'CACHE_TYPE': 'redis'})
```

#### 2. 数据库优化
```bash
# Redis 优化配置
# /etc/redis/redis.conf
maxmemory 2gb
maxmemory-policy allkeys-lru
save 900 1
save 300 10
save 60 10000
```

#### 3. 系统优化
```bash
# 增加文件描述符限制
echo "* soft nofile 65536" >> /etc/security/limits.conf
echo "* hard nofile 65536" >> /etc/security/limits.conf

# 优化内核参数
echo "net.core.somaxconn = 65535" >> /etc/sysctl.conf
sysctl -p
```

## 📖 使用指南

### 基础使用流程

#### 1. 准备测试文件
**支持的文件格式:**
- ✅ **用例模板文件** (必需): XML 格式的测试用例模板
- ✅ **历史用例文件** (可选): 之前的测试用例，用作参考
- ✅ **AW 工程模板** (可选): AW 工程的接口定义文件

**文件要求:**
- 文件格式: XML
- 文件大小: 最大 16MB
- 编码格式: UTF-8

#### 2. 上传文件
```javascript
// 支持两种上传方式

// 方式一: 拖拽上传
// 直接将文件拖拽到上传区域

// 方式二: 点击选择
// 点击"选择文件"按钮，从文件管理器选择
```

**上传界面功能:**
- 📁 拖拽上传支持
- 📋 文件格式自动验证
- 📊 上传进度实时显示
- ❌ 错误提示和处理

#### 3. 配置生成参数
**API 版本选择:**
```
v1.0 - API v1.0 (2024-01)  # 基础版本
v1.5 - API v1.5 (2024-06)  # 增强版本  
v2.0 - API v2.0 (2024-12)  # 当前推荐版本
v2.1 - API v2.1 (2025-01)  # 最新版本
```

#### 4. AI 对话交互
**对话流程:**
1. **文件分析**: AI 自动分析上传的文件内容
2. **需求收集**: 通过多轮对话了解测试需求
3. **场景确认**: 确认测试场景和优先级
4. **生成确认**: 确认开始生成测试用例

**对话技巧:**
- 🎯 **明确描述**: 清楚描述要测试的功能模块
- 📝 **场景列举**: 列出需要覆盖的测试场景
- 🔍 **重点说明**: 指出需要重点关注的测试点
- ✅ **确认生成**: 准备好后回复"开始生成"

#### 5. 测试用例生成
**生成过程:**
```
正在分析需求和文件内容... (10%)
正在规划测试用例结构... (25%)
正在生成测试步骤...     (50%)
正在优化测试用例...     (75%)
正在格式化输出...       (90%)
生成完成！             (100%)
```

#### 6. 用例编辑优化
**编辑器功能:**
- ✏️ **可视化编辑**: 直观的用例结构展示
- 🔄 **拖拽排序**: 支持步骤和组件的拖拽调整
- ➕ **添加组件**: 丰富的预设组件库
- 🔧 **参数配置**: 详细的组件参数设置
- 👁️ **实时预览**: 编辑结果实时预览

#### 7. 导出下载
**下载功能:**
- 📥 **XML 格式**: 标准的测试用例 XML 文件
- 🔒 **权限验证**: 确保只有授权用户可以下载
- 🗂️ **文件管理**: 自动清理过期的临时文件

### 高级功能使用

#### 1. 组件类型详解

**输入组件 (Input)**
```json
{
  "type": "input",
  "name": "输入用户名",
  "params": {
    "selector": "#username",     // CSS选择器
    "value": "testuser",         // 输入值
    "clear": true,               // 是否先清空
    "validation": "text",        // 验证类型
    "maxLength": 100            // 最大长度
  }
}
```

**按钮组件 (Button)**
```json
{
  "type": "button", 
  "name": "点击登录",
  "params": {
    "selector": "#login-btn",    // CSS选择器
    "action": "click",           // 操作类型
    "wait_after": 1000,         // 操作后等待时间(ms)
    "double_click": false       // 是否双击
  }
}
```

**API 组件 (API)**
```json
{
  "type": "api",
  "name": "接口调用 - 获取用户信息", 
  "params": {
    "method": "GET",            // HTTP方法
    "url": "/api/users/123",    // 请求URL
    "headers": {},              // 请求头
    "body": {},                 // 请求体
    "timeout": 30000           // 超时时间(ms)
  }
}
```

**断言组件 (Assert)**
```json
{
  "type": "assert",
  "name": "断言 - 登录成功",
  "params": {
    "type": "equals",           // 断言类型: equals/contains/exists/greater_than
    "expected": "/dashboard",   // 期望值
    "timeout": 5000,           // 超时时间(ms)
    "message": "登录失败"       // 失败消息
  }
}
```

#### 2. 预设步骤使用
**常用预设步骤:**
- 🔐 **用户认证**: 登录、注册、密码重置
- 🔍 **搜索功能**: 关键词搜索、筛选、排序
- 🛒 **电商流程**: 商品浏览、购物车、订单提交
- 📝 **表单操作**: 数据录入、验证、提交
- 🔄 **状态管理**: 数据增删改查操作

#### 3. 批量操作
**批量编辑:**
```javascript
// 批量添加相似步骤
// 1. 选择模板步骤
// 2. 点击"批量复制"
// 3. 修改参数差异
// 4. 一键应用到多个用例
```

**批量验证:**
```javascript
// 批量验证用例
// 1. 选择多个测试用例
// 2. 点击"批量验证"
// 3. 查看验证结果
// 4. 修复发现的问题
```

### 故障排除

#### 常见问题及解决方案

**1. 文件上传失败**
```
问题: "文件上传失败，请检查文件格式"
原因: 文件格式不正确或文件损坏
解决: 
- 确认文件为 XML 格式
- 检查文件是否完整
- 验证 XML 语法正确性
- 确认文件大小 < 16MB
```

**2. AI 对话无响应**
```
问题: AI 对话长时间无响应
原因: 网络问题或 AI 服务异常
解决:
- 检查网络连接
- 刷新页面重试
- 确认 Mock 模式是否启用
- 查看浏览器控制台错误信息
```

**3. 用例生成失败**
```
问题: "测试用例生成失败"
原因: 输入信息不完整或格式错误
解决:
- 重新上传文件
- 提供更详细的需求描述
- 检查文件内容格式
- 尝试使用 Mock 模式
```

**4. 下载文件异常**
```
问题: 无法下载生成的文件
原因: 会话过期或文件已清理
解决:
- 检查会话是否有效
- 重新生成测试用例
- 确认文件 ID 正确
- 联系管理员检查服务器状态
```

#### 调试模式

**启用调试模式:**
```bash
# 设置环境变量
export FLASK_ENV=development
export LOG_LEVEL=DEBUG

# 重启应用
python app.py
```

**查看详细日志:**
```bash
# 查看应用日志
tail -f logs/app.log

# 查看错误日志  
tail -f logs/error.log

# 查看访问日志
tail -f logs/access.log
```

**浏览器调试:**
```javascript
// 打开浏览器开发者工具 (F12)
// 查看 Console 标签页的错误信息
// 查看 Network 标签页的网络请求
// 查看 Application 标签页的存储信息
```

### 最佳实践

#### 1. 文件准备建议
- ✅ **标准格式**: 使用标准的 XML 测试用例格式
- ✅ **完整信息**: 确保文件包含完整的测试信息
- ✅ **清晰命名**: 使用有意义的文件名和测试用例名
- ✅ **版本管理**: 对测试文件进行版本控制

#### 2. 对话交互技巧
- 🎯 **具体明确**: 提供具体的功能描述和测试场景
- 📋 **分步说明**: 按步骤描述复杂的测试流程
- 🔍 **重点突出**: 明确指出关键的测试点和风险点
- ✅ **及时确认**: 对 AI 的理解进行及时确认和纠正

#### 3. 用例编辑优化
- 🏗️ **结构清晰**: 保持测试用例结构的清晰和逻辑性
- 🔧 **参数准确**: 确保组件参数的准确性和完整性
- 📝 **描述详细**: 为每个步骤添加清晰的描述信息
- 🧪 **覆盖全面**: 确保测试场景的全面覆盖

#### 4. 质量保证
- ✅ **定期验证**: 定期验证生成的测试用例
- 🔄 **持续优化**: 根据实际使用情况持续优化
- 📊 **效果评估**: 评估测试用例的执行效果
- 🔧 **及时更新**: 根据业务变化及时更新测试用例

## 🤝 开发贡献

### 贡献指南

我们欢迎所有形式的贡献！无论是 Bug 报告、功能建议、代码贡献还是文档改进。

#### 贡献流程

1. **Fork 项目**
   ```bash
   # 在 GitHub 上 Fork 项目到你的账户
   git clone https://github.com/your-username/ai-test-case-generator.git
   cd ai-test-case-generator
   ```

2. **创建功能分支**
   ```bash
   # 从 main 分支创建新的功能分支
   git checkout -b feature/amazing-feature
   
   # 或者修复 Bug
   git checkout -b fix/bug-description
   ```

3. **开发环境设置**
   ```bash
   # 安装开发依赖
   pip install -r requirements-dev.txt
   
   # 安装 pre-commit 钩子
   pre-commit install
   
   # 运行测试确保环境正常
   python -m pytest tests/ -v
   ```

4. **编写代码**
   - 遵循项目的代码规范
   - 添加必要的测试用例
   - 更新相关文档

5. **代码质量检查**
   ```bash
   # 代码格式化
   black .
   isort .
   
   # 代码检查
   flake8 .
   pylint services/ routes/ utils/
   
   # 类型检查
   mypy .
   
   # 运行测试
   python -m pytest tests/ -v --cov=.
   ```

6. **提交更改**
   ```bash
   # 添加更改
   git add .
   
   # 提交更改（使用有意义的提交信息）
   git commit -m "feat: add amazing new feature"
   
   # 推送到你的 Fork
   git push origin feature/amazing-feature
   ```

7. **创建 Pull Request**
   - 在 GitHub 上创建 Pull Request
   - 填写详细的 PR 描述
   - 等待代码审查和反馈

### 代码规范

#### Python 代码规范
```python
# 使用 Black 格式化代码
# 行长度限制为 88 字符
# 使用 4 个空格缩进

# 导入顺序
import os
import sys
from typing import Dict, List, Optional

import requests
from flask import Flask

from services.ai_service import AIService
```

#### 命名规范
```python
# 变量和函数：snake_case
user_name = "test"
def get_user_info():
    pass

# 类名：PascalCase  
class AIService:
    pass

# 常量：UPPER_SNAKE_CASE
MAX_FILE_SIZE = 16 * 1024 * 1024
```

#### 文档字符串
```python
def generate_test_cases(session_id: str, context: Dict[str, Any]) -> List[Dict]:
    """
    生成测试用例
    
    Args:
        session_id: 会话ID
        context: 生成上下文
        
    Returns:
        List[Dict]: 生成的测试用例列表
        
    Raises:
        ValueError: 当会话ID无效时
        AIServiceError: 当AI服务异常时
    """
    pass
```

### 测试规范

#### 测试文件结构
```
tests/
├── conftest.py              # pytest 配置和 fixtures
├── test_services/           # 服务层测试
│   ├── test_ai_service.py
│   ├── test_file_service.py
│   └── test_session_service.py
├── test_routes/             # 路由层测试
│   ├── test_generation.py
│   └── test_chat.py
└── fixtures/                # 测试数据
    ├── sample_template.xml
    └── sample_config.json
```

#### 测试用例编写
```python
import pytest
from unittest.mock import Mock, patch

class TestAIService:
    """AI服务测试类"""
    
    def test_analyze_files_success(self, ai_service, sample_files):
        """测试文件分析成功场景"""
        # Arrange
        expected_result = {"template_info": "test"}
        
        # Act
        result = ai_service.analyze_files(sample_files)
        
        # Assert
        assert result["success"] is True
        assert "template_info" in result
    
    @pytest.mark.parametrize("file_type,expected", [
        ("xml", True),
        ("txt", False),
        ("json", False)
    ])
    def test_file_validation(self, ai_service, file_type, expected):
        """测试文件格式验证"""
        result = ai_service.validate_file_type(file_type)
        assert result == expected
```

#### 测试覆盖率要求
- 新功能代码覆盖率 ≥ 90%
- 核心业务逻辑覆盖率 = 100%
- 包含单元测试、集成测试、边界测试

### 提交信息规范

使用 [Conventional Commits](https://www.conventionalcommits.org/) 规范：

```bash
# 功能添加
git commit -m "feat: add user authentication system"

# Bug 修复
git commit -m "fix: resolve file upload timeout issue"

# 文档更新
git commit -m "docs: update API documentation"

# 代码重构
git commit -m "refactor: optimize database query performance"

# 测试添加
git commit -m "test: add unit tests for chat service"

# 构建相关
git commit -m "build: update dependencies to latest versions"
```

### Issue 和 PR 模板

#### Bug 报告模板
```markdown
## Bug 描述
简要描述遇到的问题

## 复现步骤
1. 打开应用
2. 上传文件
3. 点击生成按钮
4. 看到错误信息

## 期望行为
描述你期望发生的情况

## 实际行为
描述实际发生的情况

## 环境信息
- OS: [e.g. Windows 10, macOS 12.0, Ubuntu 20.04]
- Python: [e.g. 3.9.7]
- Browser: [e.g. Chrome 96.0, Firefox 94.0]

## 附加信息
添加任何其他有助于解决问题的信息
```

#### 功能请求模板
```markdown
## 功能描述
简要描述你希望添加的功能

## 使用场景
描述这个功能的使用场景和价值

## 详细设计
如果有具体的设计想法，请详细描述

## 替代方案
是否考虑过其他解决方案？

## 附加信息
添加任何其他相关信息
```

### 开发环境配置

#### 推荐的开发工具
```bash
# 代码编辑器
- VS Code (推荐)
- PyCharm
- Vim/Neovim

# VS Code 扩展推荐
- Python
- Pylance  
- Black Formatter
- isort
- GitLens
- REST Client
```

#### 开发配置文件
```json
// .vscode/settings.json
{
    "python.formatting.provider": "black",
    "python.linting.enabled": true,
    "python.linting.pylintEnabled": true,
    "python.linting.flake8Enabled": true,
    "editor.formatOnSave": true,
    "python.sortImports.args": ["--profile", "black"]
}
```

### 发布流程

#### 版本号规范
使用 [Semantic Versioning](https://semver.org/)：
- `MAJOR.MINOR.PATCH` (例如: 1.2.3)
- MAJOR: 不兼容的 API 变更
- MINOR: 向后兼容的功能添加
- PATCH: 向后兼容的 Bug 修复

#### 发布检查清单
- [ ] 所有测试通过
- [ ] 代码覆盖率达标
- [ ] 文档已更新
- [ ] CHANGELOG 已更新
- [ ] 版本号已更新
- [ ] 安全扫描通过

## 📄 许可证

本项目采用 MIT 许可证 - 查看 [LICENSE](LICENSE) 文件了解详情。

### MIT 许可证摘要
- ✅ 商业使用
- ✅ 修改
- ✅ 分发
- ✅ 私人使用
- ❌ 责任
- ❌ 保证

## 📞 联系方式

### 项目维护者
- **项目负责人**: [Your Name](mailto:your.email@example.com)
- **技术支持**: [Support Team](mailto:support@example.com)

### 社区支持
- **GitHub Issues**: [项目问题追踪](https://github.com/your-org/ai-test-case-generator/issues)
- **讨论区**: [GitHub Discussions](https://github.com/your-org/ai-test-case-generator/discussions)
- **文档站点**: [在线文档](https://your-docs-site.com)

### 商业支持
如需商业支持、定制开发或企业级服务，请联系：
- **商务邮箱**: business@example.com
- **技术咨询**: consulting@example.com

## 🙏 致谢

### 开源项目
感谢以下开源项目的支持：
- [Flask](https://flask.palletsprojects.com/) - Web 框架
- [Redis](https://redis.io/) - 内存数据库
- [pytest](https://pytest.org/) - 测试框架
- [Hypothesis](https://hypothesis.readthedocs.io/) - 属性测试库

### 贡献者
感谢所有为项目做出贡献的开发者：
- [Contributor 1](https://github.com/contributor1)
- [Contributor 2](https://github.com/contributor2)
- [查看完整贡献者列表](https://github.com/your-org/ai-test-case-generator/contributors)

### 特别感谢
- **Dify 团队** - 提供优秀的 AI Agent 平台
- **测试团队** - 提供详细的测试反馈
- **用户社区** - 提供宝贵的使用建议

---

## 📈 更新日志

### v1.0.0 (2025-01-09)
🎉 **首个正式版本发布**

#### ✨ 新功能
- ✅ 完整的 AI 辅助测试用例生成功能
- ✅ 支持多种文件格式上传和解析
- ✅ 可视化测试用例编辑器
- ✅ 流式 AI 对话交互
- ✅ Mock 模式支持，无需外部依赖
- ✅ 完整的 API 接口和文档

#### 🔧 技术特性
- ✅ Flask 2.3+ 后端架构
- ✅ Redis 会话管理（可选）
- ✅ 135+ 测试用例，100% 通过
- ✅ 完整的错误处理和日志系统
- ✅ Docker 容器化支持
- ✅ 生产环境部署指南

#### 📚 文档完善
- ✅ 详细的使用指南和 API 文档
- ✅ 完整的部署和配置说明
- ✅ 开发贡献指南
- ✅ 故障排除和最佳实践

#### 🛡️ 安全性
- ✅ 文件上传安全验证
- ✅ 会话管理和权限控制
- ✅ 输入数据验证和清理
- ✅ 错误信息安全处理

---

**🚀 立即开始使用 AI 辅助测试用例生成工具，提升你的测试效率！**