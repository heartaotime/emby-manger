from flask import Flask, jsonify
from flask_cors import CORS
import os
from dotenv import load_dotenv

# 加载环境变量
env_path = os.path.join(os.path.dirname(__file__), '.env')
if os.path.exists(env_path):
    with open(env_path, 'r', encoding='utf-8') as f:
        for line in f:
            line = line.strip()
            if line and not line.startswith('#'):
                key, value = line.split('=', 1)
                os.environ[key] = value

app = Flask(__name__)
# 配置CORS，允许所有跨域请求
CORS(app, resources={r"/api/*": {"origins": "*", "methods": ["GET", "POST", "PUT", "DELETE", "OPTIONS"], "allow_headers": ["Content-Type", "Authorization"]}})

# 导入数据库初始化
from utils.database import init_db

# 导入各个模块的蓝图
from api.auth import auth_bp
from api.users import users_bp
from api.emby import emby_bp
from api.plugins import plugins_bp

# 注册蓝图
app.register_blueprint(auth_bp)
app.register_blueprint(users_bp)
app.register_blueprint(emby_bp)
app.register_blueprint(plugins_bp)

# 初始化数据库
init_db()

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)
