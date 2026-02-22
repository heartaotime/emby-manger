from flask import Blueprint, request, jsonify
from utils.auth import generate_token
from config.auth import ADMIN_USERNAME, ADMIN_PASSWORD

# 创建蓝图
auth_bp = Blueprint('auth', __name__, url_prefix='/api')

# 登录API
@auth_bp.route('/login', methods=['POST'])
def login():
    auth = request.json
    
    if not auth or not auth.get('username') or not auth.get('password'):
        return jsonify({'success': False, 'message': '请提供用户名和密码'}), 401
    
    # 验证管理员账号密码
    if auth['username'] == ADMIN_USERNAME and auth['password'] == ADMIN_PASSWORD:
        # 生成JWT token
        token = generate_token(ADMIN_USERNAME)
        
        return jsonify({
            'success': True,
            'message': '登录成功',
            'token': token,
            'user': {
                'username': ADMIN_USERNAME
            }
        })
    
    return jsonify({'success': False, 'message': '用户名或密码错误'}), 401

# 测试路由
@auth_bp.route('/test', methods=['GET'])
def test():
    return jsonify({'message': '后端服务正在运行'})
