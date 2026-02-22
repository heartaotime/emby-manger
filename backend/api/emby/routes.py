from flask import Blueprint, jsonify
from utils.auth import token_required
from services.emby_service import check_emby_connection

# 创建蓝图
emby_bp = Blueprint('emby', __name__, url_prefix='/emby')

# 检查 Emby 连接状态
@emby_bp.route('/check-connection', methods=['GET'])
@token_required
def check_connection(current_user):
    result = check_emby_connection()
    return jsonify(result)
