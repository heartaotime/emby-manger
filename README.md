# Emby 管理器

一个基于 Flask + Vue 的 Emby 媒体服务器用户管理系统，支持用户的创建、管理、过期控制等功能。

## 功能特性

- 📦 **用户管理**：创建、编辑、删除、启用/禁用用户
- 🔄 **Emby 同步**：自动从 Emby 服务器同步用户信息
- ⏰ **过期控制**：设置用户过期时间，自动禁用过期用户
- 🔗 **Emby 集成**：与 Emby 服务器实时通信，管理用户权限
- 🐳 **Docker 部署**：支持 Docker 容器化部署，一键启动
- 📱 **响应式界面**：基于 Vue 的现代化前端界面

## 技术栈

- **后端**：Python Flask
- **前端**：Vue 3 + Vite
- **数据库**：MySQL
- **部署**：Docker + Docker Compose

## 快速开始

### 前提条件

- Docker 和 Docker Compose 已安装
- Emby 服务器已部署并运行
- MySQL 数据库服务（或使用 Docker 启动）

### 环境配置

1. **克隆项目**

```bash
git clone <repository-url>
cd emby-manger
```

2. **配置环境变量**

#### 方法一：使用 Docker Compose 环境变量（推荐）

编辑 `docker-compose.yml` 文件，修改以下环境变量：

```yaml
environment:
  - FLASK_ENV=production
  - DB_HOST=100.64.64.1      # 数据库主机地址
  - DB_PORT=3306             # 数据库端口
  - DB_USER=emby_manager     # 数据库用户名
  - DB_PASSWORD=emby_manager # 数据库密码
  - DB_NAME=emby_manager     # 数据库名称
  - EMBY_URL=http://100.64.64.1:9000  # Emby 服务器地址
  - EMBY_API_KEY=2a42f8230f9a49fa9df317048572ba09  # Emby API 密钥
  - EMBY_TEMPLATE_USER_ID=bdb7f79dbbb24839aee075811af0625a  # 模板用户 ID
```

#### 方法二：使用 .env 文件

复制 `.env.example` 文件为 `.env`，然后修改其中的配置：

```bash
cd backend
copy .env.example .env
# 编辑 .env 文件，填入实际配置
```

`.env` 文件包含以下配置项：

```
# 数据库配置
DB_HOST=localhost
DB_PORT=3306
DB_USER=your_database_username
DB_PASSWORD=your_database_password
DB_NAME=emby_manager

# Emby 配置
EMBY_URL=http://your_emby_server:8096
EMBY_API_KEY=your_emby_api_key
EMBY_TEMPLATE_USER_ID=your_template_user_id
```

### 启动服务

使用 Docker Compose 启动服务：

```bash
docker-compose up -d
```

服务将在 `http://localhost:5000` 上运行。

## 详细安装

### 方法一：Docker 部署（推荐）

1. **修改配置**

编辑 `docker-compose.yml` 文件，配置数据库和 Emby 服务器信息。

2. **启动容器**

```bash
docker-compose up -d --build
```

3. **验证服务**

访问 `http://localhost:5000` 查看服务是否正常运行。

### 方法二：本地部署

1. **安装依赖**

```bash
# 后端依赖
cd backend
pip install -r requirements.txt

# 前端依赖
cd ../frontend
npm install
```

2. **构建前端**

```bash
npm run build
```

3. **启动后端**

```bash
cd ../backend
python app.py
```

## API 接口

### 核心接口

- **GET /api/test**：测试后端服务是否正常运行
- **GET /api/emby/check-connection**：检查 Emby 服务器连接状态
- **POST /api/sync/users**：从 Emby 同步用户信息
- **GET /api/users**：获取所有用户列表（支持搜索和筛选）
- **POST /api/users**：创建新用户
- **PUT /api/users/<id>**：更新用户信息（主要是过期时间）
- **PUT /api/users/<id>/status**：启用/禁用用户
- **DELETE /api/users/<id>**：删除用户
- **POST /api/check-expire**：检查并禁用过期用户

### 响应格式

所有 API 接口返回统一的 JSON 格式：

```json
{
  "success": true,  // 操作是否成功
  "message": "操作成功",  // 操作结果消息
  "data": []  // 返回的数据（可选）
}
```

## 使用说明

### 1. 首次使用

1. 启动服务后，访问 `http://localhost:5000`
2. 点击「同步用户」按钮，从 Emby 服务器同步现有用户
3. 系统会自动创建数据库表结构

### 2. 创建用户

1. 点击「创建用户」按钮
2. 填写用户名、密码（可选，默认 123456）、过期时间（可选）
3. 点击「保存」，系统会在 Emby 服务器和本地数据库中创建用户

### 3. 管理用户

- **编辑用户**：点击用户列表中的「编辑」按钮，修改用户信息
- **启用/禁用用户**：点击用户列表中的「启用」/「禁用」按钮
- **删除用户**：点击用户列表中的「删除」按钮

### 4. 检查过期用户

点击「检查过期」按钮，系统会自动禁用所有已过期的用户。

## 配置说明

### Emby API 密钥获取

1. 登录 Emby 服务器管理界面
2. 进入「设置」→「API 密钥」
3. 点击「新建 API 密钥」，输入名称后创建
4. 复制生成的 API 密钥到 `docker-compose.yml` 文件中

### 模板用户 ID

模板用户用于在创建新用户时复制权限设置：

1. 登录 Emby 服务器管理界面
2. 进入「用户」页面
3. 选择一个已有的用户作为模板
4. 在浏览器地址栏中查看 URL，其中包含用户 ID（如 `http://emby-server:8096/web/index.html#!/users.html?userId=xxxxxxxxxxxxxxxxxxxx`）
5. 复制该用户 ID 到 `docker-compose.yml` 文件中

## 常见问题

### 1. 无法连接到 Emby 服务器

- 检查 `EMBY_URL` 是否正确
- 检查 `EMBY_API_KEY` 是否有效
- 确保 Emby 服务器正在运行且可以访问

### 2. 创建用户失败

- 检查 `EMBY_TEMPLATE_USER_ID` 是否正确设置
- 确保模板用户存在且权限正确
- 查看 Docker 容器日志获取详细错误信息

### 3. 数据库连接失败

- 检查数据库主机、端口、用户名、密码是否正确
- 确保 MySQL 数据库服务正在运行
- 确保数据库用户有足够的权限

### 4. 用户同步失败

- 检查 Emby 服务器连接状态
- 确保 Emby API 密钥有足够的权限
- 查看 Docker 容器日志获取详细错误信息

## 日志管理

查看 Docker 容器日志：

```bash
docker-compose logs -f
```

## 开发指南

### 后端开发

1. 进入后端目录：`cd backend`
2. 安装依赖：`pip install -r requirements.txt`
3. 运行开发服务器：`python app.py`

### 前端开发

1. 进入前端目录：`cd frontend`
2. 安装依赖：`npm install`
3. 运行开发服务器：`npm run dev`
4. 构建生产版本：`npm run build`

## 项目结构

```
emby-manger/
├── backend/            # 后端代码
│   ├── app.py          # 主应用文件
│   └── requirements.txt # 依赖文件
├── frontend/           # 前端代码
│   ├── public/         # 静态资源
│   ├── src/            # 源代码
│   │   ├── components/ # 组件
│   │   ├── App.vue     # 根组件
│   │   └── main.js     # 入口文件
│   ├── index.html      # HTML 模板
│   ├── package.json    # 前端依赖
│   └── vite.config.js  # Vite 配置
├── .dockerignore       # Docker 忽略文件
├── .gitignore          # Git 忽略文件
├── Dockerfile          # Docker 构建文件
├── docker-compose.yml  # Docker Compose 配置
└── README.md           # 项目说明
```

## 许可证

[MIT License](LICENSE)

## 更新日志

### v1.0.0

- 初始版本
- 支持用户的创建、编辑、删除、启用/禁用
- 支持从 Emby 服务器同步用户
- 支持用户过期时间管理
- 支持 Docker 部署

## 贡献

欢迎提交 Issue 和 Pull Request 来改进这个项目！

## 联系方式

如果您有任何问题或建议，请通过以下方式联系我们：

- Issue 讨论：在 GitHub 仓库中创建 Issue
- 邮箱：<your-email@example.com>

---

**说明**：本项目仅用于个人学习和研究，请勿用于商业用途。