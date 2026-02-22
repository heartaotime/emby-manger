from flask import Blueprint, jsonify
import subprocess
import os
import threading
import time
from utils.auth import token_required

# 创建蓝图
plugins_bp = Blueprint('plugins', __name__, url_prefix='/api')

# 全局变量，用于保存189share脚本进程
script_process = None

# 执行189share脚本
@plugins_bp.route('/189share/execute', methods=['POST'])
@token_required
def execute_189share(current_user):
    try:
        # 脚本路径
        script_path = os.path.join(os.path.dirname(__file__), '..', '..', 'plugin', 'cloudpan189share.py')
        
        # 日志文件路径
        log_dir = os.path.join(os.path.dirname(__file__), '..', '..', 'logs')
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
@plugins_bp.route('/189share/logs', methods=['GET'])
@token_required
def get_189share_logs(current_user):
    try:
        # 日志文件路径
        log_dir = os.path.join(os.path.dirname(__file__), '..', '..', 'logs')
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
@plugins_bp.route('/189share/stop', methods=['POST'])
@token_required
def stop_189share(current_user):
    try:
        global script_process
        if script_process:
            # 终止进程
            script_process.terminate()
            try:
                # 等待进程终止
                script_process.wait(timeout=5)
            except subprocess.TimeoutExpired:
                # 如果进程在5秒内没有终止，强制杀死
                script_process.kill()
            script_process = None
            return jsonify({'success': True, 'message': '189share脚本已成功中断'})
        else:
            return jsonify({'success': False, 'message': '没有正在执行的189share脚本'})
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)}), 500
