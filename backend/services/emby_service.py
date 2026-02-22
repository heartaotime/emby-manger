import requests
import json
from config.emby import emby_config
from utils.logger import logger

def check_emby_connection():
    """
    检查Emby连接状态
    :return: dict 包含连接状态和服务器信息
    """
    url = f"{emby_config['url']}/emby/System/Info"
    headers = {
        'X-Emby-Token': emby_config['api_key'],
        'Accept': 'application/json'
    }
    
    try:
        response = requests.get(url, headers=headers, timeout=10)
        logger.info(f"📡 检查连接状态码: {response.status_code}")
        try:
            content_str = response.content.decode('utf-8')
            content_json = json.loads(content_str)
            logger.debug(f"📄 检查连接响应内容: {json.dumps(content_json, ensure_ascii=False, indent=2)}")
        except:
            logger.debug(f"📄 检查连接响应内容: {response.content}")
        
        if response.status_code == 200:
            system_info = response.json()
            return {
                'success': True,
                'connected': True,
                'message': '成功连接到Emby服务器',
                'server_info': {
                    'name': system_info.get('ServerName', 'Unknown'),
                    'version': system_info.get('Version', 'Unknown'),
                    'operating_system': system_info.get('OperatingSystem', 'Unknown')
                }
            }
        else:
            error_msg = f'连接Emby服务器失败: 状态码 {response.status_code}，响应: {response.content}'
            logger.error(f"❌ {error_msg}")
            return {
                'success': True,
                'connected': False,
                'message': error_msg
            }
    except Exception as e:
        error_msg = f'连接Emby服务器错误: {str(e)}'
        logger.error(f"❌ {error_msg}")
        return {
            'success': True,
            'connected': False,
            'message': error_msg
        }

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
        logger.info(f"📡 获取用户信息状态码: {response.status_code}")
        try:
            content_str = response.content.decode('utf-8')
            content_json = json.loads(content_str)
            logger.debug(f"📄 获取用户信息响应内容: {json.dumps(content_json, ensure_ascii=False, indent=2)}")
        except:
            logger.debug(f"📄 获取用户信息响应内容: {response.content}")
        
        if response.status_code == 200:
            user_data = response.json()
            return True, user_data
        else:
            error_msg = f"获取失败，状态码: {response.status_code}，响应: {response.content}"
            logger.error(f"❌ Emby 用户 {emby_id} {error_msg}")
            return False, error_msg
    except Exception as e:
        error_msg = f"获取错误: {str(e)}"
        logger.error(f"❌ Emby 用户 {emby_id} {error_msg}")
        return False, error_msg

def get_emby_users():
    """
    获取Emby用户列表
    :return: (success, users_list or error_message)
    """
    url = f"{emby_config['url']}/emby/Users"
    headers = {
        'X-Emby-Token': emby_config['api_key'],
        'Accept': 'application/json'
    }
    
    try:
        response = requests.get(url, headers=headers, timeout=10)
        logger.info(f"📡 获取用户列表状态码: {response.status_code}")
        try:
            content_str = response.content.decode('utf-8')
            content_json = json.loads(content_str)
            logger.debug(f"📄 获取用户列表响应内容: {json.dumps(content_json, ensure_ascii=False, indent=2)}")
        except:
            logger.debug(f"📄 获取用户列表响应内容: {response.content}")
        
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
                logger.error(f"❌ {error_msg}")
                return False, error_msg
        else:
            error_msg = f"获取用户列表失败，状态码: {response.status_code}，响应: {response.content}"
            logger.error(f"❌ {error_msg}")
            return False, error_msg
    except Exception as e:
        error_msg = f"获取用户列表错误: {str(e)}"
        logger.error(f"❌ {error_msg}")
        return False, error_msg

def get_emby_user_details(user_id):
    """
    获取单个 Emby 用户的详细信息，包括注册时间
    :param user_id: Emby用户ID
    :return: dict 用户详细信息
    """
    success, result = get_emby_user_info(user_id)
    if success:
        user_details = result
        logger.info(f"📦 获取用户详细信息: {user_details.get('Name')}")
        return user_details
    else:
        logger.error(f"❌ 获取用户详细信息失败: {result}")
        return None

def create_emby_user(user_data):
    """
    创建Emby用户
    :param user_data: 用户数据
    :return: (success, user_info or error_message)
    """
    user_name = user_data.get('Name')
    logger.info(f"📋 创建 Emby 用户: {user_name}")
    
    # 获取配置的模板用户 ID
    template_user_id = emby_config.get('template_user_id', '')
    logger.info(f"🔑 配置的模板用户 ID: {template_user_id}")
    
    # 获取用户密码
    user_password = user_data.get('Password', '123456')
    logger.info(f"🔐 获取到的用户密码: {user_password}")
    
    # 必须配置模板用户 ID
    if not template_user_id:
        error_msg = "未配置模板用户 ID，请在 .env 文件中设置 EMBY_TEMPLATE_USER_ID"
        logger.error(f"❌ {error_msg}")
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
    
    logger.info(f"✨ 从模板创建用户: {user_name}，使用模板 ID {template_user_id}")
    logger.info(f"🔗 请求 URL: {url}")
    logger.debug(f"📋 请求消息体: {json.dumps(template_data, ensure_ascii=False, indent=2)}")
    # logger.debug(f"📝 请求头: {json.dumps(headers, ensure_ascii=False, indent=2)}")
    
    response = requests.post(url, json=template_data, headers=headers)
    logger.info(f"📡 从模板创建状态码: {response.status_code}")
    try:
        content_str = response.content.decode('utf-8')
        content_json = json.loads(content_str)
        # logger.debug(f"📄 从模板创建响应内容: {json.dumps(content_json, ensure_ascii=False, indent=2)}")
    except:
        logger.debug(f"📄 从模板创建响应内容: {response.content}")
    # logger.debug(f"📝 响应头: {json.dumps(dict(response.headers), ensure_ascii=False, indent=2)}")
    
    # 必须使用模板创建成功才算成功
    if response.status_code not in [200, 204]:
        error_msg = f"从模板创建用户失败: {response.status_code}，响应: {response.content}"
        logger.error(f"❌ {error_msg}")
        logger.warning(f"⚠️  请检查模板用户ID是否正确，以及Emby服务器是否支持从模板创建用户")
        return False, {'error': error_msg}
    
    # 处理成功响应
    try:
        # 检查响应状态码和内容
        if response.status_code == 204:
            # 204 No Content，没有响应体
            logger.info(f"📦 从模板创建响应: No Content (204)")
            # 由于没有响应体，无法获取用户ID，这里需要处理
            error_msg = "从模板创建用户成功，但无法获取用户ID（响应为204 No Content）"
            logger.warning(f"⚠️ {error_msg}")
            return False, {'error': error_msg}
        else:
            # 有响应体的情况
            response_json = response.json()
            # logger.debug(f"📦 从模板创建响应: {json.dumps(response_json, ensure_ascii=False, indent=2)}")
            
            # 获取新创建的用户ID
            user_id = response_json.get('Id')
            if user_id:
                logger.info(f"✅ 用户创建成功，用户ID: {user_id}")
                
                # 从前端传入的值获取密码，同时处理大小写
                # 优先使用大写的Password键，因为在create_user函数中传递的是大写的Password
                user_password = user_data.get('Password', '123456')
                logger.info(f"🔐 初始化用户密码为: {user_password}")
                logger.debug(f"📋 前端传入的完整数据: {json.dumps(user_data, ensure_ascii=False, indent=2)}")
                password_url = f"{emby_config['url']}/emby/Users/{user_id}/Password"
                password_data = {
                    # 'CurrentPw': None,
                    'NewPw': user_password
                    # 'ResetPassword': True
                }
                
                logger.info(f"🔗 密码设置 URL: {password_url}")
                logger.debug(f"📋 密码设置数据: {json.dumps(password_data, ensure_ascii=False, indent=2)}")
                
                password_response = requests.post(password_url, json=password_data, headers=headers)
                logger.info(f"📡 密码设置状态码: {password_response.status_code}")
                try:
                    content_str = password_response.content.decode('utf-8')
                    content_json = json.loads(content_str)
                    logger.debug(f"📄 密码设置响应内容: {json.dumps(content_json, ensure_ascii=False, indent=2)}")
                except:
                    logger.debug(f"📄 密码设置响应内容: {password_response.content}")
                
                # 密码设置成功
                if password_response.status_code in [200, 204]:
                    logger.info(f"✅ 密码设置成功")
                else:
                    logger.warning(f"⚠️  密码设置失败，但用户已创建成功")
            
            return True, response_json
    except Exception as e:
        error_msg = f"解析模板创建响应错误: {e}"
        logger.error(f"❌ {error_msg}")
        return False, {'error': error_msg}

def update_emby_user_policy(user_id, user_data):
    """
    更新Emby用户策略
    :param user_id: Emby用户ID
    :param user_data: 用户策略数据
    :return: (success, error_message or None)
    """
    url = f"{emby_config['url']}/emby/Users/{user_id}/Policy"
    headers = {
        'X-Emby-Token': emby_config['api_key'],
        'Content-Type': 'application/json',
        'Accept': 'application/json'
    }
    
    logger.info(f"🔄 更新 Emby 用户: {user_id}")
    logger.info(f"🔗 请求 URL: {url}")
    logger.debug(f"📋 请求数据: {json.dumps(user_data, ensure_ascii=False, indent=2)}")
    
    try:
        response = requests.post(url, json=user_data, headers=headers, timeout=10)
        logger.info(f"📡 更新状态码: {response.status_code}")
        try:
            content_str = response.content.decode('utf-8')
            content_json = json.loads(content_str)
            logger.debug(f"📄 更新响应内容: {json.dumps(content_json, ensure_ascii=False, indent=2)}")
        except:
            logger.debug(f"📄 更新响应内容: {response.content}")
        
        if response.status_code in [200, 204]:
            logger.info(f"✅ Emby 用户 {user_id} 更新成功")
            return True, None
        else:
            error_msg = f"更新失败，状态码: {response.status_code}，响应: {response.content}"
            logger.error(f"❌ Emby 用户 {user_id} {error_msg}")
            return False, error_msg
    except Exception as e:
        error_msg = f"更新错误: {str(e)}"
        logger.error(f"❌ Emby 用户 {user_id} {error_msg}")
        return False, error_msg

def delete_emby_user(user_id):
    """
    删除Emby用户
    :param user_id: Emby用户ID
    :return: (success, error_message or None)
    """
    url = f"{emby_config['url']}/emby/Users/{user_id}"
    headers = {
        'X-Emby-Token': emby_config['api_key'],
        'Accept': 'application/json'
    }
    
    try:
        response = requests.delete(url, headers=headers, timeout=10)
        logger.info(f"📡 删除用户状态码: {response.status_code}")
        try:
            content_str = response.content.decode('utf-8')
            content_json = json.loads(content_str)
            logger.debug(f"📄 删除响应内容: {json.dumps(content_json, ensure_ascii=False, indent=2)}")
        except:
            logger.debug(f"📄 删除响应内容: {response.content}")
        
        if response.status_code == 204:
            logger.info(f"✅ Emby 用户 {user_id} 删除成功")
            return True, None
        else:
            error_msg = f"删除失败，状态码: {response.status_code}，响应: {response.content}"
            logger.error(f"❌ Emby 用户 {user_id} {error_msg}")
            return False, error_msg
    except Exception as e:
        error_msg = f"删除错误: {str(e)}"
        logger.error(f"❌ Emby 用户 {user_id} {error_msg}")
        return False, error_msg
