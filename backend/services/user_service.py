import datetime
import pymysql
from utils.database import get_db_connection
from utils.logger import logger
from services.emby_service import get_emby_users, get_emby_user_details, create_emby_user, update_emby_user_policy, delete_emby_user

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
        from services.emby_service import get_emby_user_info
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
        logger.info(f"{result_icon} {status_icon} 已更新 Emby 用户 {emby_id} 状态: {'已禁用' if not is_active else '已启用'}, 成功: {emby_update_success}")
        
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
        logger.error(f"❌ 启用/禁用用户错误: {e}")
        return False, str(e)

def sync_users():
    """
    从Emby同步用户到数据库
    :return: (success, message)
    """
    try:
        emby_success, emby_result = get_emby_users()
        if not emby_success:
            return False, f'从Emby同步用户失败: {emby_result}'
        
        emby_users = emby_result
        conn = get_db_connection()
        cursor = conn.cursor()
        
        synced_count = 0
        updated_count = 0
        for user in emby_users:
            emby_id = user['Id']
            name = user['Name']
            
            # 打印用户分隔符
            logger.info(f"\n{'='*50}")
            logger.info(f"👤 正在处理用户: {name} (ID: {emby_id})")
            logger.info(f"{'='*50}")
            
            # 获取用户详细信息，包括注册时间和激活状态
            user_details = get_emby_user_details(emby_id)
            date_created = None
            is_active = True
            
            if user_details:
                # 获取注册时间
                if 'DateCreated' in user_details:
                    date_created = user_details['DateCreated']
                    logger.info(f"📅 注册时间: {date_created}")
                    # 转换ISO 8601格式为MySQL datetime格式
                    try:
                        # 解析ISO 8601格式
                        dt = datetime.datetime.fromisoformat(date_created.replace('Z', '+00:00'))
                        # 转换为MySQL支持的datetime格式
                        date_created = dt.strftime('%Y-%m-%d %H:%M:%S')
                        logger.info(f"🔄 转换后注册时间: {date_created}")
                    except Exception as e:
                        logger.warning(f"⚠️  时间格式转换失败: {e}")
                        date_created = None
                
                # 获取激活状态，使用 $.Policy.IsDisabled
                if 'Policy' in user_details and 'IsDisabled' in user_details['Policy']:
                    is_active = not user_details['Policy']['IsDisabled']
                    logger.info(f"🔐 激活状态: {'启用' if is_active else '禁用'}")
            
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
        
        return True, f'已从Emby同步 {synced_count} 个用户，更新了 {updated_count} 个现有用户'
    except Exception as e:
        return False, str(e)

def get_users(search_query='', status_filter=None, expire_status=None, page=1, page_size=10):
    """
    获取用户列表
    :param search_query: 搜索关键词
    :param status_filter: 状态过滤
    :param expire_status: 过期状态过滤
    :param page: 页码，默认为1
    :param page_size: 每页大小，默认为10
    :return: dict 包含用户列表和总记录数
    """
    try:
        conn = get_db_connection()
        cursor = conn.cursor(pymysql.cursors.DictCursor)
        
        # 构建查询
        base_query = 'SELECT * FROM users WHERE state = 1'
        count_query = 'SELECT COUNT(*) as total FROM users WHERE state = 1'
        params = []
        
        if search_query:
            base_query += ' AND name LIKE %s'
            count_query += ' AND name LIKE %s'
            params.append('%' + search_query + '%')
        
        if status_filter is not None:
            # 确保正确处理布尔值
            is_active = status_filter.lower() == 'true'
            base_query += ' AND is_active = %s'
            count_query += ' AND is_active = %s'
            params.append(is_active)
        
        if expire_status == 'active':
            # 只查询未过期的用户
            base_query += ' AND (expire_date IS NULL OR expire_date >= NOW())'
            count_query += ' AND (expire_date IS NULL OR expire_date >= NOW())'
        elif expire_status == 'expired':
            # 只查询已过期的用户
            base_query += ' AND expire_date < NOW()'
            count_query += ' AND expire_date < NOW()'
        
        # 计算分页偏移量
        offset = (page - 1) * page_size
        base_query += ' LIMIT %s OFFSET %s'
        params.extend([page_size, offset])
        
        # 执行计数查询
        cursor.execute(count_query, params[:-2])  # 排除LIMIT和OFFSET参数
        total_result = cursor.fetchone()
        total = total_result['total'] if total_result else 0
        
        # 执行分页查询
        cursor.execute(base_query, params)
        users = cursor.fetchall()
        
        cursor.close()
        conn.close()
        
        # 格式化用户数据中的日期时间字段
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
        
        return {
            'data': formatted_users,
            'total': total,
            'page': page,
            'page_size': page_size
        }
    except Exception as e:
        logger.error(f"❌ 获取用户列表错误: {e}")
        return {
            'data': [],
            'total': 0,
            'page': page,
            'page_size': page_size
        }

def create_user(user_data):
    """
    创建用户
    :param user_data: 用户数据
    :return: (success, message)
    """
    try:
        name = user_data['name']
        password = user_data.get('password', '123456')  # 默认密码
        email = user_data.get('email', '')
        expire_date = user_data.get('expire_date', None)
        
        # Convert ISO datetime string to MySQL DATETIME format
        if expire_date:
            # Handle ISO format (2026-02-20T01:45:00.000Z)
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
            return False, f'在Emby中创建用户失败: {error_message}'
        
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
        
        return True, '用户创建成功'
    except Exception as e:
        return False, str(e)

def update_user(user_id, user_data):
    """
    更新用户
    :param user_id: 用户ID
    :param user_data: 用户数据
    :return: (success, message)
    """
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # 获取用户信息
        cursor.execute('SELECT emby_id, is_active FROM users WHERE id = %s AND state = 1', (user_id,))
        user = cursor.fetchone()
        if not user:
            cursor.close()
            conn.close()
            return False, '用户不存在'
        
        emby_id, current_active = user
        
        # 只处理过期时间的修改
        if 'expire_date' in user_data:
            expire_date = user_data['expire_date']
            
            # Convert ISO datetime string to MySQL DATETIME format
            if expire_date:
                # Handle ISO format (2026-02-20T01:45:00.000Z)
                if isinstance(expire_date, str):
                    # Parse ISO string to datetime object
                    try:
                        dt = datetime.datetime.fromisoformat(expire_date.replace('Z', '+00:00'))
                        # Convert to MySQL DATETIME format
                        expire_date = dt.strftime('%Y-%m-%d %H:%M:%S')
                    except:
                        pass
            
            # 根据过期时间自动设置激活状态
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
                    return False, message
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
        
        return True, '用户更新成功'
    except Exception as e:
        return False, str(e)

def update_user_status(user_id, is_active):
    """
    更新用户状态
    :param user_id: 用户ID
    :param is_active: 是否启用
    :return: (success, message)
    """
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # 获取用户信息
        cursor.execute('SELECT emby_id, is_active FROM users WHERE id = %s AND state = 1', (user_id,))
        user = cursor.fetchone()
        if not user:
            cursor.close()
            conn.close()
            return False, '用户不存在'
        
        # 使用公共方法更新用户状态
        success, message = toggle_user_status(user_id, is_active)
        
        cursor.close()
        conn.close()
        
        return success, message
    except Exception as e:
        return False, str(e)

def delete_user(user_id):
    """
    删除用户
    :param user_id: 用户ID
    :return: (success, message)
    """
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # 获取用户的 Emby ID
        cursor.execute('SELECT emby_id FROM users WHERE id = %s AND state = 1', (user_id,))
        user = cursor.fetchone()
        if not user:
            cursor.close()
            conn.close()
            return False, '用户不存在'
        
        emby_id = user[0]
        
        # 从 Emby 中删除用户
        delete_success, error_msg = delete_emby_user(emby_id)
        if not delete_success:
            return False, f'从Emby中删除用户失败: {error_msg}' if error_msg else '从Emby中删除用户失败'
        
        # 从数据库中标记用户为已删除（更新state字段为0）
        cursor.execute('UPDATE users SET state = 0 WHERE id = %s', (user_id,))
        conn.commit()
        
        cursor.close()
        conn.close()
        
        return True, '用户删除成功'
    except Exception as e:
        return False, str(e)

def check_expire():
    """
    检查用户有效期并禁用过期用户
    :return: (success, message)
    """
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
            
            logger.info(f"🔍 检查过期用户: {name} (ID: {user_id}, Emby ID: {emby_id})")
            
            # 使用公共方法禁用用户
            logger.info(f"🚫 正在禁用用户: {name}")
            success, message = toggle_user_status(user_id, False)
            if success:
                disabled_count += 1
                logger.info(f"✅ 用户 {name} 已成功禁用")
            else:
                logger.error(f"❌ 禁用用户 {name} 失败: {message}")
        
        conn.commit()
        
        cursor.close()
        conn.close()
        
        return True, f'已禁用 {disabled_count} 个过期用户'
    except Exception as e:
        return False, str(e)
