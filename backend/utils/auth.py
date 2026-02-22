import jwt
from datetime import datetime, timedelta
from functools import wraps
from flask import request, jsonify
from config.auth import SECRET_KEY

def generate_token(username):
    """
    生成JWT token
    :param username: 用户名
    :return: token字符串
    """
    token = jwt.encode(
        {'username': username, 'exp': datetime.utcnow() + timedelta(hours=24)},
        SECRET_KEY,
        algorithm='HS256'
    )
    return token

def verify_token(token):
    """
    验证JWT token
    :param token: token字符串
    :return: (success, payload)
    """
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=['HS256'])
        return True, payload
    except:
        return False, None

def token_required(f):
    """
    鉴权中间件
    """
    @wraps(f)
    def decorated(*args, **kwargs):
        token = None
        
        # 从请求头获取token
        if 'Authorization' in request.headers:
            token = request.headers['Authorization'].split(' ')[1] if len(request.headers['Authorization'].split(' ')) > 1 else None
        
        if not token:
            return jsonify({'success': False, 'message': '未提供认证令牌'}), 401
        
        try:
            # 解码token
            data = jwt.decode(token, SECRET_KEY, algorithms=['HS256'])
            current_user = data['username']
        except jwt.ExpiredSignatureError:
            return jsonify({'success': False, 'message': '令牌已过期'}), 401
        except jwt.InvalidTokenError:
            return jsonify({'success': False, 'message': '无效的认证令牌'}), 401
        except Exception as e:
            return jsonify({'success': False, 'message': f'认证错误: {str(e)}'}), 401
        
        return f(current_user, *args, **kwargs)
    return decorated
