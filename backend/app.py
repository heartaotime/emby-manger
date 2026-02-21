from flask import Flask, jsonify, request, make_response
from flask_cors import CORS
import pymysql
import requests
import os
import datetime
import subprocess
from dotenv import load_dotenv
import jwt
from functools import wraps

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

# 数据库配置
db_config = {
    'host': os.getenv('DB_HOST', 'localhost'),
    'port': int(os.getenv('DB_PORT', '3306')),
    'user': os.getenv('DB_USER', 'root'),
    'password': os.getenv('DB_PASSWORD', 'password'),
    'database': os.getenv('DB_NAME', 'emby_manager')
}

# 全局变量，用于保存189share脚本进程
script_process = None

# Emby 配置
emby_config = {
    'url': os.getenv('EMBY_URL', 'http://localhost:8096'),
    'api_key': os.getenv('EMBY_API_KEY', ''),
    'template_user_id': os.getenv('EMBY_TEMPLATE_USER_ID', '')
}

# JWT配置
SECRET_KEY = os.urandom(24).hex()
ADMIN_USERNAME = os.getenv('ADMIN_USERNAME', 'admin')
ADMIN_PASSWORD = os.getenv('ADMIN_PASSWORD', 'admin123')

def get_db_connection():
    return pymysql.connect(**db_config)

# 鉴权中间件
def token_required(f):
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
        except:
            return jsonify({'success': False, 'message': '无效的认证令牌'}), 401
        
        return f(current_user, *args, **kwargs)
    return decorated

# 初始化数据库
def init_db():
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # 创建用户表
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS users (
            id INT AUTO_INCREMENT PRIMARY KEY,
            emby_id VARCHAR(255) UNIQUE,
            name VARCHAR(255) NOT NULL,
            email VARCHAR(255),
            password VARCHAR(255),
            is_active BOOLEAN DEFAULT TRUE,
            state TINYINT DEFAULT 1,
            expire_date DATETIME,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
            updated_at DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
        )
        ''')
        
        conn.commit()
        cursor.close()
        conn.close()
        print("数据库初始化成功")
    except Exception as e:
        print(f"数据库初始化失败: {e}")
        print("服务将继续运行，但数据库相关功能可能受限")

# 登录API
@app.route('/api/login', methods=['POST'])
def login():
    auth = request.json
    
    if not auth or not auth.get('username') or not auth.get('password'):
        return jsonify({'success': False, 'message': '请提供用户名和密码'}), 401
    
    # 验证管理员账号密码
    if auth['username'] == ADMIN_USERNAME and auth['password'] == ADMIN_PASSWORD:
        # 生成JWT token
        token = jwt.encode(
            {'username': ADMIN_USERNAME, 'exp': datetime.datetime.utcnow() + datetime.timedelta(hours=24)},
            SECRET_KEY,
            algorithm='HS256'
        )
        
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
@app.route('/api/test', methods=['GET'])
def test():
    return jsonify({'message': '后端服务正在运行'})

# 检查 Emby 连接状态
@app.route('/api/emby/check-connection', methods=['GET'])
@token_required
def check_emby_connection(current_user):
    url = f"{emby_config['url']}/emby/System/Info"
    headers = {
        'X-Emby-Token': emby_config['api_key'],
        'Accept': 'application/json'
    }
    
    try:
        response = requests.get(url, headers=headers, timeout=10)
        print(f"📡 检查连接状态码: {response.status_code}")
        try:
            content_str = response.content.decode('utf-8')
            import json
            content_json = json.loads(content_str)
            print(f"📄 检查连接响应内容: {json.dumps(content_json, ensure_ascii=False, indent=2)}")
        except:
            print(f"📄 检查连接响应内容: {response.content}")
        
        if response.status_code == 200:
            system_info = response.json()
            return jsonify({
                'success': True,
                'connected': True,
                'message': '成功连接到Emby服务器',
                'server_info': {
                    'name': system_info.get('ServerName', 'Unknown'),
                    'version': system_info.get('Version', 'Unknown'),
                    'operating_system': system_info.get('OperatingSystem', 'Unknown')
                }
            })
        else:
            error_msg = f'连接Emby服务器失败: 状态码 {response.status_code}，响应: {response.content}'
            print(f"❌ {error_msg}")
            return jsonify({
                'success': True,
                'connected': False,
                'message': error_msg
            })
    except Exception as e:
        error_msg = f'连接Emby服务器错误: {str(e)}'
        print(f"❌ {error_msg}")
        return jsonify({
            'success': True,
            'connected': False,
            'message': error_msg
        })

# 获取Emby用户信息
def get_emby_user_info(emby_id):
    """
    获取Emby用户信息
    :param emby_id: Emby用户ID
    :return: (success, user_data or error_message)
    """
    try:
        url = f"{emby_config['url']}/emby/Users/{emby_id}"
        headers = {
            'X-Emby-Token': emby_config['api_key'],
            'Accept': 'application/json'
        }
        response = requests.get(url, headers=headers, timeout=10)
        print(f"📡 获取用户信息状态码: {response.status_code}")
        try:
            content_str = response.content.decode('utf-8')
            import json
            content_json = json.loads(content_str)
            print(f"📄 获取用户信息响应内容: {json.dumps(content_json, ensure_ascii=False, indent=2)}")
        except:
            print(f"📄 获取用户信息响应内容: {response.content}")
        
        if response.status_code == 200:
            user_data = response.json()
            return True, user_data
        else:
            error_msg = f"获取失败，状态码: {response.status_code}，响应: {response.content}"
            print(f"❌ Emby 用户 {emby_id} {error_msg}")
            return False, error_msg
    except Exception as e:
        error_msg = f"获取错误: {str(e)}"
        print(f"❌ Emby 用户 {emby_id} {error_msg}")
        return False, error_msg

# 公共方法：启用/禁用用户
def toggle_user_status(user_id, is_active):
    """
    启用/禁用用户
    :param user_id: 用户ID
    :param is_active: 是否启用
    :return: (success, message)
    """
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # 获取用户信息
        cursor.execute('SELECT emby_id FROM users WHERE id = %s AND state = 1', (user_id,))
        user = cursor.fetchone()
        if not user:
            cursor.close()
            conn.close()
            return False, '用户不存在'
        
        emby_id = user[0]
        
        # 先获取用户的完整策略信息
        success, result = get_emby_user_info(emby_id)
        if not success:
            cursor.close()
            conn.close()
            return False, result
        
        user_data = result
        # 获取用户的策略信息
        user_policy = user_data.get('Policy')
        if not user_policy:
            cursor.close()
            conn.close()
            return False, '获取用户策略信息失败'
        
        # 只修改IsDisabled字段
        user_policy['IsDisabled'] = not is_active
        emby_user_data = user_policy
        
        # 更新 Emby 用户状态
        emby_update_success, error_msg = update_emby_user_policy(emby_id, emby_user_data)
        status_icon = "🔒" if not is_active else "🔓"
        result_icon = "✅" if emby_update_success else "❌"
        print(f"{result_icon} {status_icon} 已更新 Emby 用户 {emby_id} 状态: {'已禁用' if not is_active else '已启用'}, 成功: {emby_update_success}")
        
        # 只有在Emby更新成功后才更新数据库
        if emby_update_success:
            # 更新数据库
            cursor.execute('''
                UPDATE users 
                SET is_active = %s, updated_at = CURRENT_TIMESTAMP 
                WHERE id = %s
            ''', (is_active, user_id))
            conn.commit()
            
            cursor.close()
            conn.close()
            
            return True, '用户状态更新成功'
        else:
            # Emby更新失败
            cursor.close()
            conn.close()
            return False, f'在Emby中更新用户状态失败: {error_msg}' if error_msg else '在Emby中更新用户状态失败'
    except Exception as e:
        print(f"❌ 启用/禁用用户错误: {e}")
        return False, str(e)

# Emby API 集成
def get_emby_users():
    url = f"{emby_config['url']}/emby/Users"
    headers = {
        'X-Emby-Token': emby_config['api_key'],
        'Accept': 'application/json'
    }
    
    try:
        response = requests.get(url, headers=headers, timeout=10)
        print(f"📡 获取用户列表状态码: {response.status_code}")
        try:
            content_str = response.content.decode('utf-8')
            import json
            content_json = json.loads(content_str)
            print(f"📄 获取用户列表响应内容: {json.dumps(content_json, ensure_ascii=False, indent=2)}")
        except:
            print(f"📄 获取用户列表响应内容: {response.content}")
        
        if response.status_code == 200:
            try:
                data = response.json()
                # Check if response is directly a list or has an 'Items' key
                if isinstance(data, list):
                    return True, data
                elif 'Items' in data:
                    return True, data['Items']
                else:
                    # Return empty list if unexpected structure
                    return True, []
            except Exception as e:
                error_msg = f"解析 Emby 用户响应错误: {e}"
                print(f"❌ {error_msg}")
                return False, error_msg
        else:
            error_msg = f"获取用户列表失败，状态码: {response.status_code}，响应: {response.content}"
            print(f"❌ {error_msg}")
            return False, error_msg
    except Exception as e:
        error_msg = f"获取用户列表错误: {str(e)}"
        print(f"❌ {error_msg}")
        return False, error_msg

def get_emby_user_details(user_id):
    """获取单个 Emby 用户的详细信息，包括注册时间"""
    success, result = get_emby_user_info(user_id)
    if success:
        user_details = result
        print(f"📦 获取用户详细信息: {user_details.get('Name')}")
        return user_details
    else:
        print(f"❌ 获取用户详细信息失败: {result}")
        return None

def create_emby_user(user_data):
    user_name = user_data.get('Name')
    print(f"📋 创建 Emby 用户: {user_name}")
    
    # 获取配置的模板用户 ID
    template_user_id = emby_config.get('template_user_id', '')
    print(f"🔑 配置的模板用户 ID: {template_user_id}")
    
    # 获取用户密码
    user_password = user_data.get('Password', '123456')
    print(f"🔐 获取到的用户密码: {user_password}")
    
    # 必须配置模板用户 ID
    if not template_user_id:
        error_msg = "未配置模板用户 ID，请在 .env 文件中设置 EMBY_TEMPLATE_USER_ID"
        print(f"❌ {error_msg}")
        return False, {'error': error_msg}
    
    # 使用正确的Emby API端点创建用户
    # 根据官方文档，应该使用 /Users/New 端点并设置 CopyFromUserId 参数
    url = f"{emby_config['url']}/emby/Users/New"
    headers = {
        'X-Emby-Token': emby_config['api_key'],
        'Content-Type': 'application/json',
        'Accept': 'application/json'
    }
    
    # 构建请求数据 - 使用官方文档指定的参数格式
    # 优先使用小写字段名（前端传入的），然后使用大写字段名
    
    template_data = {
        'Name': user_name,
        'CopyFromUserId': template_user_id,
        'UserCopyOptions': [
            'UserPolicy'
        ]
    }
    
    print(f"✨ 从模板创建用户: {user_name}，使用模板 ID {template_user_id}")
    print(f"🔗 请求 URL: {url}")
    import json
    print(f"📋 请求消息体: {json.dumps(template_data, ensure_ascii=False, indent=2)}")
    # print(f"📝 请求头: {json.dumps(headers, ensure_ascii=False, indent=2)}")
    
    response = requests.post(url, json=template_data, headers=headers)
    print(f"📡 从模板创建状态码: {response.status_code}")
    try:
        content_str = response.content.decode('utf-8')
        import json
        content_json = json.loads(content_str)
        # print(f"📄 从模板创建响应内容: {json.dumps(content_json, ensure_ascii=False, indent=2)}")
    except:
        print(f"📄 从模板创建响应内容: {response.content}")
    import json
    # print(f"📝 响应头: {json.dumps(dict(response.headers), ensure_ascii=False, indent=2)}")
    
    # 必须使用模板创建成功才算成功
    if response.status_code not in [200, 204]:
        error_msg = f"从模板创建用户失败: {response.status_code}，响应: {response.content}"
        print(f"❌ {error_msg}")
        print(f"⚠️  请检查模板用户ID是否正确，以及Emby服务器是否支持从模板创建用户")
        return False, {'error': error_msg}
    
    # 处理成功响应
    try:
        # 检查响应状态码和内容
        if response.status_code == 204:
            # 204 No Content，没有响应体
            print(f"📦 从模板创建响应: No Content (204)")
            # 由于没有响应体，无法获取用户ID，这里需要处理
            error_msg = "从模板创建用户成功，但无法获取用户ID（响应为204 No Content）"
            print(f"⚠️ {error_msg}")
            return False, {'error': error_msg}
        else:
            # 有响应体的情况
            response_json = response.json()
            import json
            # print(f"📦 从模板创建响应: {json.dumps(response_json, ensure_ascii=False, indent=2)}")
            
            # 获取新创建的用户ID
            user_id = response_json.get('Id')
            if user_id:
                print(f"✅ 用户创建成功，用户ID: {user_id}")
                
                # 从前端传入的值获取密码，同时处理大小写
                # 优先使用大写的Password键，因为在create_user函数中传递的是大写的Password
                user_password = user_data.get('Password', '123456')
                import json
                print(f"🔐 初始化用户密码为: {user_password}")
                print(f"📋 前端传入的完整数据: {json.dumps(user_data, ensure_ascii=False, indent=2)}")
                password_url = f"{emby_config['url']}/emby/Users/{user_id}/Password"
                password_data = {
                    # 'CurrentPw': None,
                    'NewPw': user_password
                    # 'ResetPassword': True
                }
                
                import json
                print(f"🔗 密码设置 URL: {password_url}")
                print(f"📋 密码设置数据: {json.dumps(password_data, ensure_ascii=False, indent=2)}")
                
                password_response = requests.post(password_url, json=password_data, headers=headers)
                print(f"📡 密码设置状态码: {password_response.status_code}")
                try:
                    content_str = password_response.content.decode('utf-8')
                    import json
                    content_json = json.loads(content_str)
                    print(f"📄 密码设置响应内容: {json.dumps(content_json, ensure_ascii=False, indent=2)}")
                except:
                    print(f"📄 密码设置响应内容: {password_response.content}")
                
                if password_response.status_code == 204:
                    print(f"✅ 密码设置成功")
                else:
                    print(f"⚠️  密码设置失败，但用户已创建成功")
            
            return True, response_json
    except Exception as e:
        error_msg = f"解析模板创建响应错误: {e}"
        print(f"❌ {error_msg}")
        return False, {'error': error_msg}

def update_emby_user_policy(user_id, user_data):
    url = f"{emby_config['url']}/emby/Users/{user_id}/Policy"
    headers = {
        'X-Emby-Token': emby_config['api_key'],
        'Content-Type': 'application/json',
        'Accept': 'application/json'
    }
    
    print(f"🔄 更新 Emby 用户: {user_id}")
    import json
    print(f"🔗 请求 URL: {url}")
    print(f"📋 请求数据: {json.dumps(user_data, ensure_ascii=False, indent=2)}")
    
    try:
        response = requests.post(url, json=user_data, headers=headers, timeout=10)
        print(f"📡 更新状态码: {response.status_code}")
        try:
            content_str = response.content.decode('utf-8')
            import json
            content_json = json.loads(content_str)
            print(f"📄 更新响应内容: {json.dumps(content_json, ensure_ascii=False, indent=2)}")
        except:
            print(f"📄 更新响应内容: {response.content}")
        
        if response.status_code in [200, 204]:
            print(f"✅ Emby 用户 {user_id} 更新成功")
            return True, None
        else:
            error_msg = f"更新失败，状态码: {response.status_code}，响应: {response.content}"
            print(f"❌ Emby 用户 {user_id} {error_msg}")
            return False, error_msg
    except Exception as e:
        error_msg = f"更新错误: {str(e)}"
        print(f"❌ Emby 用户 {user_id} {error_msg}")
        return False, error_msg

def delete_emby_user(user_id):
    url = f"{emby_config['url']}/emby/Users/{user_id}"
    headers = {
        'X-Emby-Token': emby_config['api_key'],
        'Accept': 'application/json'
    }
    
    try:
        response = requests.delete(url, headers=headers, timeout=10)
        print(f"📡 删除用户状态码: {response.status_code}")
        try:
            content_str = response.content.decode('utf-8')
            import json
            content_json = json.loads(content_str)
            print(f"📄 删除响应内容: {json.dumps(content_json, ensure_ascii=False, indent=2)}")
        except:
            print(f"📄 删除响应内容: {response.content}")
        
        if response.status_code == 204:
            print(f"✅ Emby 用户 {user_id} 删除成功")
            return True, None
        else:
            error_msg = f"删除失败，状态码: {response.status_code}，响应: {response.content}"
            print(f"❌ Emby 用户 {user_id} {error_msg}")
            return False, error_msg
    except Exception as e:
        error_msg = f"删除错误: {str(e)}"
        print(f"❌ Emby 用户 {user_id} {error_msg}")
        return False, error_msg

# 用户同步路由
@app.route('/api/sync/users', methods=['POST'])
@token_required
def sync_users(current_user):
    try:
        emby_success, emby_result = get_emby_users()
        if not emby_success:
            return jsonify({'success': False, 'message': f'从Emby同步用户失败: {emby_result}'}), 500
        
        emby_users = emby_result
        conn = get_db_connection()
        cursor = conn.cursor()
        
        synced_count = 0
        updated_count = 0
        for user in emby_users:
            emby_id = user['Id']
            name = user['Name']
            
            # 打印用户分隔符
            print(f"\n{'='*50}")
            print(f"👤 正在处理用户: {name} (ID: {emby_id})")
            print(f"{'='*50}")
            
            # 获取用户详细信息，包括注册时间和激活状态
            user_details = get_emby_user_details(emby_id)
            date_created = None
            is_active = True
            
            if user_details:
                # 获取注册时间
                if 'DateCreated' in user_details:
                    date_created = user_details['DateCreated']
                    print(f"📅 注册时间: {date_created}")
                    # 转换ISO 8601格式为MySQL datetime格式
                    try:
                        # 解析ISO 8601格式
                        dt = datetime.datetime.fromisoformat(date_created.replace('Z', '+00:00'))
                        # 转换为MySQL支持的datetime格式
                        date_created = dt.strftime('%Y-%m-%d %H:%M:%S')
                        print(f"🔄 转换后注册时间: {date_created}")
                    except Exception as e:
                        print(f"⚠️  时间格式转换失败: {e}")
                        date_created = None
                
                # 获取激活状态，使用 $.Policy.IsDisabled
                if 'Policy' in user_details and 'IsDisabled' in user_details['Policy']:
                    is_active = not user_details['Policy']['IsDisabled']
                    print(f"🔐 激活状态: {'启用' if is_active else '禁用'}")
            
            # 检查用户是否已存在
            cursor.execute('SELECT id FROM users WHERE emby_id = %s', (emby_id,))
            existing_user = cursor.fetchone()
            
            if not existing_user:
                # 插入新用户
                # 如果注册时间为空，数据库会使用 DEFAULT CURRENT_TIMESTAMP
                cursor.execute('''
                INSERT INTO users (emby_id, name, is_active, state, created_at)
                VALUES (%s, %s, %s, %s, %s)
                ''', (emby_id, name, is_active, 1, date_created))
                synced_count += 1
            else:
                # 更新现有用户
                cursor.execute('''
                    UPDATE users 
                    SET name = %s, is_active = %s, state = %s, created_at = %s 
                    WHERE emby_id = %s
                    ''', (name, is_active, 1, date_created, emby_id))
                updated_count += 1
        
        conn.commit()
        cursor.close()
        conn.close()
        
        return jsonify({'success': True, 'message': f'已从Emby同步 {synced_count} 个用户，更新了 {updated_count} 个现有用户'})
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)}), 500

# 获取所有用户
@app.route('/api/users', methods=['GET'])
@token_required
def get_users(current_user):
    try:
        conn = get_db_connection()
        cursor = conn.cursor(pymysql.cursors.DictCursor)
        
        # 获取搜索参数
        search_query = request.args.get('search', '')
        status_filter = request.args.get('status', None)
        expire_status = request.args.get('expire_status', None)
        
        # 构建查询
        query = 'SELECT * FROM users WHERE state = 1'
        params = []
        
        if search_query:
            query += ' AND name LIKE %s'
            params.append('%' + search_query + '%')
        
        if status_filter is not None:
            # 确保正确处理布尔值
            is_active = status_filter.lower() == 'true'
            query += ' AND is_active = %s'
            params.append(is_active)
        
        if expire_status == 'active':
            # 只查询未过期的用户
            query += ' AND (expire_date IS NULL OR expire_date >= NOW())'
        elif expire_status == 'expired':
            # 只查询已过期的用户
            query += ' AND expire_date < NOW()'
        
        cursor.execute(query, params)
        users = cursor.fetchall()
        
        cursor.close()
        conn.close()
        
        # 格式化用户数据中的日期时间字段
        try:
            formatted_users = []
            for user in users:
                # 检查用户数据类型
                if isinstance(user, dict):
                    # 如果是字典，使用键来访问元素
                    formatted_user = {
                        'id': user.get('id'),
                        'emby_id': user.get('emby_id'),
                        'name': user.get('name'),
                        'email': user.get('email'),
                        'password': user.get('password'),
                        'is_active': user.get('is_active'),
                        'state': user.get('state'),
                        'expire_date': user.get('expire_date').strftime('%Y-%m-%d %H:%M:%S') if user.get('expire_date') else None,
                        'created_at': user.get('created_at').strftime('%Y-%m-%d %H:%M:%S') if user.get('created_at') else None,
                        'updated_at': user.get('updated_at').strftime('%Y-%m-%d %H:%M:%S') if user.get('updated_at') else None
                    }
                else:
                    # 如果是元组，使用索引来访问元素
                    # 假设元组的顺序是: id, emby_id, name, email, password, is_active, state, expire_date, created_at, updated_at
                    formatted_user = {
                        'id': user[0],
                        'emby_id': user[1],
                        'name': user[2],
                        'email': user[3],
                        'password': user[4],
                        'is_active': user[5],
                        'state': user[6],
                        'expire_date': user[7].strftime('%Y-%m-%d %H:%M:%S') if user[7] else None,
                        'created_at': user[8].strftime('%Y-%m-%d %H:%M:%S'),
                        'updated_at': user[9].strftime('%Y-%m-%d %H:%M:%S')
                    }
                formatted_users.append(formatted_user)
            
            return jsonify({'success': True, 'data': formatted_users})
        except Exception as e:
            # 返回原始用户数据，避免因格式化错误而导致API失败
            return jsonify({'success': True, 'data': users})
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)}), 500

# 创建用户
@app.route('/api/users', methods=['POST'])
@token_required
def create_user(current_user):
    try:
        data = request.json
        name = data['name']
        password = data.get('password', '123456')  # 默认密码
        email = data.get('email', '')
        expire_date = data.get('expire_date', None)
        
        # Convert ISO datetime string to MySQL DATETIME format
        if expire_date:
            # Handle ISO format (2026-02-20T01:45:00.000Z)
            import datetime
            if isinstance(expire_date, str):
                # Parse ISO string to datetime object
                try:
                    dt = datetime.datetime.fromisoformat(expire_date.replace('Z', '+00:00'))
                    # Convert to MySQL DATETIME format
                    expire_date = dt.strftime('%Y-%m-%d %H:%M:%S')
                except:
                    pass
        
        # 在 Emby 中创建用户
        emby_user_data = {
            'Name': name,
            'Password': password
        }
        
        success, emby_response = create_emby_user(emby_user_data)
        if not success:
            error_message = emby_response.get('error', '未知错误')
            return jsonify({'success': False, 'message': f'在Emby中创建用户失败: {error_message}'}), 500
        
        emby_id = emby_response['Id']
        
        # 在数据库中创建用户
        conn = get_db_connection()
        cursor = conn.cursor()
        
        cursor.execute('''
        INSERT INTO users (emby_id, name, email, password, is_active, state, expire_date)
        VALUES (%s, %s, %s, %s, %s, %s, %s)
        ''', (emby_id, name, email, password, True, 1, expire_date))
        
        conn.commit()
        cursor.close()
        conn.close()
        
        return jsonify({'success': True, 'message': '用户创建成功'})
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)}), 500

# 更新用户（只修改过期时间）
@app.route('/api/users/<int:user_id>', methods=['PUT'])
@token_required
def update_user(current_user, user_id):
    try:
        data = request.json
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # 获取用户信息
        cursor.execute('SELECT emby_id, is_active FROM users WHERE id = %s AND state = 1', (user_id,))
        user = cursor.fetchone()
        if not user:
            return jsonify({'success': False, 'message': '用户不存在'}), 404
        
        emby_id, current_active = user
        
        # 只处理过期时间的修改
        if 'expire_date' in data:
            expire_date = data['expire_date']
            
            # Convert ISO datetime string to MySQL DATETIME format
            if expire_date:
                # Handle ISO format (2026-02-20T01:45:00.000Z)
                import datetime
                if isinstance(expire_date, str):
                    # Parse ISO string to datetime object
                    try:
                        dt = datetime.datetime.fromisoformat(expire_date.replace('Z', '+00:00'))
                        # Convert to MySQL DATETIME format
                        expire_date = dt.strftime('%Y-%m-%d %H:%M:%S')
                    except:
                        pass
            
            # 根据过期时间自动设置激活状态
            import datetime
            now = datetime.datetime.now()
            
            if not expire_date:
                # 没有过期时间，设置为启用
                new_active = True
            else:
                # 有过期时间，比较是否在当前时间之后
                expire_dt = datetime.datetime.strptime(expire_date, '%Y-%m-%d %H:%M:%S')
                new_active = expire_dt > now
            
            # 更新 Emby 用户状态（如果状态有变化）
            status_update_success = True
            if new_active != current_active:
                # 使用公共方法更新用户状态
                status_update_success, message = toggle_user_status(user_id, new_active)
                if not status_update_success:
                    # 状态更新失败，返回错误
                    return jsonify({'success': False, 'message': message}), 500
            else:
                # 状态没有变化，只更新过期时间
                cursor.execute('''
                    UPDATE users 
                    SET expire_date = %s, updated_at = CURRENT_TIMESTAMP 
                    WHERE id = %s
                ''', (expire_date, user_id))
                conn.commit()
        
        cursor.close()
        conn.close()
        
        return jsonify({'success': True, 'message': '用户更新成功'})
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)}), 500

# 启用/禁用用户
@app.route('/api/users/<int:user_id>/status', methods=['PUT'])
@token_required
def update_user_status(current_user, user_id):
    try:
        data = request.json
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # 获取用户信息
        cursor.execute('SELECT emby_id, is_active FROM users WHERE id = %s AND state = 1', (user_id,))
        user = cursor.fetchone()
        if not user:
            return jsonify({'success': False, 'message': '用户不存在'}), 404
        
        emby_id, current_active = user
        
        # 只处理启用/禁用状态的修改
        if 'is_active' in data:
            new_active = data['is_active']
            
            # 使用公共方法更新用户状态
            success, message = toggle_user_status(user_id, new_active)
            
            cursor.close()
            conn.close()
            
            if success:
                return jsonify({'success': True, 'message': message})
            else:
                return jsonify({'success': False, 'message': message}), 500
        
        cursor.close()
        conn.close()
        
        return jsonify({'success': False, 'message': '请提供is_active参数'}), 400
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)}), 500

# 删除用户
@app.route('/api/users/<int:user_id>', methods=['DELETE'])
@token_required
def delete_user(current_user, user_id):
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # 获取用户的 Emby ID
        cursor.execute('SELECT emby_id FROM users WHERE id = %s AND state = 1', (user_id,))
        user = cursor.fetchone()
        if not user:
            return jsonify({'success': False, 'message': '用户不存在'}), 404
        
        emby_id = user[0]
        
        # 从 Emby 中删除用户
        delete_success, error_msg = delete_emby_user(emby_id)
        if not delete_success:
            return jsonify({'success': False, 'message': f'从Emby中删除用户失败: {error_msg}' if error_msg else '从Emby中删除用户失败'}), 500
        
        # 从数据库中标记用户为已删除（更新state字段为0）
        cursor.execute('UPDATE users SET state = 0 WHERE id = %s', (user_id,))
        conn.commit()
        
        cursor.close()
        conn.close()
        
        return jsonify({'success': True, 'message': '用户删除成功'})
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)}), 500

# 检查用户有效期并禁用过期用户
@app.route('/api/check-expire', methods=['POST'])
@token_required
def check_expire(current_user):
    try:
        conn = get_db_connection()
        cursor = conn.cursor(pymysql.cursors.DictCursor)
        
        # 查询过期且仍处于激活状态的用户
        cursor.execute('''
        SELECT id, emby_id, name 
        FROM users 
        WHERE expire_date < NOW() AND is_active = TRUE AND state = 1
        ''')
        expired_users = cursor.fetchall()
        
        disabled_count = 0
        
        for user in expired_users:
            user_id = user['id']
            emby_id = user['emby_id']
            name = user['name']
            
            print(f"🔍 检查过期用户: {name} (ID: {user_id}, Emby ID: {emby_id})")
            
            # 使用公共方法禁用用户
            print(f"🚫 正在禁用用户: {name}")
            success, message = toggle_user_status(user_id, False)
            if success:
                disabled_count += 1
                print(f"✅ 用户 {name} 已成功禁用")
            else:
                print(f"❌ 禁用用户 {name} 失败: {message}")
        
        conn.commit()
        
        cursor.close()
        conn.close()
        
        return jsonify({'success': True, 'message': f'已禁用 {disabled_count} 个过期用户'})
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)}), 500

# 执行189share脚本
@app.route('/api/189share/execute', methods=['POST'])
@token_required
def execute_189share(current_user):
    try:
        import subprocess
        import os
        import threading
        import time
        
        # 脚本路径
        script_path = os.path.join(os.path.dirname(__file__), 'plugin', 'cloudpan189share.py')
        
        # 日志文件路径
        log_dir = os.path.join(os.path.dirname(__file__), 'logs')
        os.makedirs(log_dir, exist_ok=True)
        log_file = os.path.join(log_dir, '189share.log')
        
        # 执行脚本的函数
        def run_script():
            global script_process
            # 同时输出到文件和控制台
            class Tee:
                def __init__(self, file_obj):
                    self.file_obj = file_obj
                def write(self, data):
                    self.file_obj.write(data)
                    print(data, end='')
                def flush(self):
                    self.file_obj.flush()
            
            # 尝试打开日志文件，添加错误处理
            try:
                # 使用 'w' 模式直接覆盖写入，不需要先删除文件
                with open(log_file, 'w', encoding='utf-8') as f:
                    tee = Tee(f)
                    # 设置环境变量，确保 Python 以 UTF-8 编码运行
                    env = os.environ.copy()
                    env['PYTHONIOENCODING'] = 'utf-8'
                    # 保存进程对象，以便后续可以中断
                    # 不使用 shell=True，直接执行命令，以便正确终止进程
                    script_process = subprocess.Popen(['python', script_path], 
                                                   stdout=tee, 
                                                   stderr=tee, 
                                                   cwd=os.path.dirname(__file__),
                                                   shell=False,
                                                   env=env)
                    print(f"[INFO] 脚本进程已启动，PID: {script_process.pid}")
                    # 等待进程完成
                    script_process.wait()
            except Exception as e:
                print(f"[ERROR] 无法写入日志文件: {str(e)}")
                # 如果无法写入日志文件，仅输出到控制台
                env = os.environ.copy()
                env['PYTHONIOENCODING'] = 'utf-8'
                # 不使用 shell=True，直接执行命令，以便正确终止进程
                script_process = subprocess.Popen(['python', script_path], 
                                               cwd=os.path.dirname(__file__),
                                               shell=False,
                                               env=env)
                print(f"[INFO] 脚本进程已启动，PID: {script_process.pid}")
                script_process.wait()
            finally:
                # 执行完成后清空进程对象
                script_process = None
        
        # 在后台线程中执行脚本
        thread = threading.Thread(target=run_script)
        thread.daemon = True
        thread.start()
        
        return jsonify({'success': True, 'message': '189share脚本已开始执行，请稍候查看日志'})
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)}), 500

# 获取189share脚本执行日志
@app.route('/api/189share/logs', methods=['GET'])
@token_required
def get_189share_logs(current_user):
    try:
        import os
        
        # 日志文件路径
        log_dir = os.path.join(os.path.dirname(__file__), 'logs')
        log_file = os.path.join(log_dir, '189share.log')
        
        # 读取日志内容
        if os.path.exists(log_file):
            with open(log_file, 'r', encoding='utf-8', errors='ignore') as f:
                logs = f.read()
        else:
            logs = '脚本尚未执行或日志文件不存在'
        
        return jsonify({'success': True, 'logs': logs})
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)}), 500

# 中断189share脚本执行
@app.route('/api/189share/stop', methods=['POST'])
@token_required
def stop_189share(current_user):
    try:
        # 使用全局变量 script_process
        global script_process
        
        print("ℹ️ [INFO] 开始处理脚本中断请求")
        
        if script_process:
            # 保存当前进程对象的引用
            current_process = script_process
            # 立即清空全局变量，避免其他请求干扰
            script_process = None
            
            process_status = current_process.poll()
            print(f"ℹ️ [INFO] 进程状态: {'运行中' if process_status is None else f'已结束，退出码: {process_status}'}")
            
            if process_status is None:
                print(f"⚠️ [INFO] 正在终止进程 (PID: {current_process.pid})...")
                # 终止进程
                current_process.terminate()
                
                try:
                    # 等待进程终止
                    print("ℹ️ [INFO] 等待进程终止，最多等待5秒...")
                    current_process.wait(timeout=5)
                    final_status = current_process.poll()
                    print(f"✅ [INFO] 进程已成功终止，退出码: {final_status}")
                except subprocess.TimeoutExpired:
                    # 如果超时，强制杀死进程
                    print("⚠️ [INFO] 进程终止超时，尝试强制杀死...")
                    try:
                        current_process.kill()
                        print("✅ [INFO] 进程已强制杀死")
                    except Exception as kill_error:
                        print(f"❌ [ERROR] 强制杀死进程时发生错误: {str(kill_error)}")
                except Exception as wait_error:
                    print(f"❌ [ERROR] 等待进程终止时发生错误: {str(wait_error)}")
                finally:
                    # 进程处理完成
                    del current_process
                    print("ℹ️ [INFO] 脚本中断处理完成")
                
                return jsonify({'success': True, 'message': '脚本执行已中断'})
            else:
                # 进程已经结束
                del current_process
                print("ℹ️ [INFO] 脚本进程已结束，无需中断")
                return jsonify({'success': False, 'message': '脚本进程已结束'})
        else:
            print("ℹ️ [INFO] 没有正在执行的脚本进程")
            return jsonify({'success': False, 'message': '没有正在执行的脚本'})
    except Exception as e:
        print(f"❌ [ERROR] 中断脚本时发生错误: {str(e)}")
        # 确保进程对象被清空
        script_process = None
        return jsonify({'success': False, 'message': str(e)}), 500



# 配置静态文件服务
from flask import send_from_directory
import os

@app.route('/')
def index():
    return send_from_directory('static', 'index.html')

@app.route('/<path:path>')
def static_file(path):
    return send_from_directory('static', path)

if __name__ == '__main__':
    init_db()
    app.run(host='0.0.0.0', port=5000, debug=True)
