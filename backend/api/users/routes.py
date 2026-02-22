from flask import Blueprint, request, jsonify
from utils.auth import token_required
from services.user_service import sync_users, get_users, create_user, update_user, update_user_status, delete_user, check_expire

# 创建蓝图
users_bp = Blueprint('users', __name__, url_prefix='/api')

# 用户同步路由
@users_bp.route('/sync/users', methods=['POST'])
@token_required
def sync_users_route(current_user):
    success, message = sync_users()
    if success:
        return jsonify({'success': True, 'message': message})
    else:
        return jsonify({'success': False, 'message': message}), 500

# 获取所有用户
@users_bp.route('/users', methods=['GET'])
@token_required
def get_users_route(current_user):
    try:
        # 获取搜索参数
        search_query = request.args.get('search', '')
        status_filter = request.args.get('status', None)
        expire_status = request.args.get('expire_status', None)
        
        users = get_users(search_query, status_filter, expire_status)
        return jsonify({'success': True, 'data': users})
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)}), 500

# 创建用户
@users_bp.route('/users', methods=['POST'])
@token_required
def create_user_route(current_user):
    try:
        data = request.json
        success, message = create_user(data)
        if success:
            return jsonify({'success': True, 'message': message})
        else:
            return jsonify({'success': False, 'message': message}), 500
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)}), 500

# 更新用户（只修改过期时间）
@users_bp.route('/users/<int:user_id>', methods=['PUT'])
@token_required
def update_user_route(current_user, user_id):
    try:
        data = request.json
        success, message = update_user(user_id, data)
        if success:
            return jsonify({'success': True, 'message': message})
        else:
            return jsonify({'success': False, 'message': message}), 500
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)}), 500

# 启用/禁用用户
@users_bp.route('/users/<int:user_id>/status', methods=['PUT'])
@token_required
def update_user_status_route(current_user, user_id):
    try:
        data = request.json
        if 'is_active' not in data:
            return jsonify({'success': False, 'message': '请提供is_active参数'}), 400
        
        is_active = data['is_active']
        success, message = update_user_status(user_id, is_active)
        if success:
            return jsonify({'success': True, 'message': message})
        else:
            return jsonify({'success': False, 'message': message}), 500
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)}), 500

# 删除用户
@users_bp.route('/users/<int:user_id>', methods=['DELETE'])
@token_required
def delete_user_route(current_user, user_id):
    try:
        success, message = delete_user(user_id)
        if success:
            return jsonify({'success': True, 'message': message})
        else:
            return jsonify({'success': False, 'message': message}), 500
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)}), 500

# 检查用户有效期并禁用过期用户
@users_bp.route('/check-expire', methods=['POST'])
@token_required
def check_expire_route(current_user):
    try:
        success, message = check_expire()
        if success:
            return jsonify({'success': True, 'message': message})
        else:
            return jsonify({'success': False, 'message': message}), 500
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)}), 500
