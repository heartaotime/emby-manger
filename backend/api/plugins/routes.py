from flask import Blueprint, jsonify, Response
import subprocess
import os
import threading
import time
import datetime
from utils.auth import token_required
from utils.logger import Logger

# 创建日志记录器
logger = Logger('plugins')

# 创建蓝图
plugins_bp = Blueprint('plugins', __name__, url_prefix='')

# 全局变量，用于保存脚本进程，使用字典来支持多个插件
script_processes = {}

# 执行插件脚本
@plugins_bp.route('/<plugin_name>/execute', methods=['POST'])
@token_required
def execute_plugin(current_user, plugin_name):
    try:
        # 插件脚本映射
        plugin_scripts = {
            '189share': 'cloudpan189share.py'
            # 可以在这里添加更多插件
        }
        
        # 检查插件是否存在
        if plugin_name not in plugin_scripts:
            return jsonify({'success': False, 'message': f'插件 {plugin_name} 不存在'}), 404
        
        # 脚本路径
        script_filename = plugin_scripts[plugin_name]
        script_path = os.path.join(os.path.dirname(__file__), '..', '..', 'plugin', script_filename)
        
        # 检查脚本文件是否存在
        if not os.path.exists(script_path):
            return jsonify({'success': False, 'message': f'插件脚本文件不存在: {script_filename}'}), 404
        
        # 执行脚本的函数
        def run_script():
            try:
                # 计算正确的backend目录路径
                backend_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
                
                # 设置环境变量，确保 Python 以 UTF-8 编码运行，并添加backend目录到PYTHONPATH
                env = os.environ.copy()
                env['PYTHONIOENCODING'] = 'utf-8'
                # 添加backend目录到PYTHONPATH，确保能够正确导入utils模块
                env['PYTHONPATH'] = backend_dir + ';' + env.get('PYTHONPATH', '')
                
                # 保存进程对象，以便后续可以中断
                # 不使用 shell=True，直接执行命令，以便正确终止进程
                process = subprocess.Popen(['python', script_path], 
                                           cwd=backend_dir,
                                           shell=False,
                                           env=env)
                
                # 打印调试信息
                logger.info(f"[{plugin_name}] 工作目录: {backend_dir}")
                logger.info(f"[{plugin_name}] PYTHONPATH: {env['PYTHONPATH']}")
                
                # 保存进程到字典
                script_processes[plugin_name] = process
                logger.info(f"[{plugin_name}] 脚本进程已启动，PID: {process.pid}")
                
                # 等待进程完成
                process.wait()
            except Exception as e:
                logger.error(f"[{plugin_name}] 执行脚本时出错: {str(e)}")
            finally:
                # 执行完成后从字典中移除进程
                if plugin_name in script_processes:
                    del script_processes[plugin_name]
                logger.info(f"[{plugin_name}] 脚本执行完成")
        
        # 在后台线程中执行脚本
        thread = threading.Thread(target=run_script)
        thread.daemon = True
        thread.start()
        
        return jsonify({'success': True, 'message': f'{plugin_name} 插件已开始执行，请稍候查看日志'})
    except Exception as e:
        logger.error(f"启动插件时出错: {str(e)}")
        return jsonify({'success': False, 'message': str(e)}), 500

# 获取插件脚本执行日志
@plugins_bp.route('/<plugin_name>/logs', methods=['GET'])
@token_required
def get_plugin_logs(current_user, plugin_name):
    try:
        # 插件日志文件映射
        plugin_log_files = {
            '189share': 'cloudpan189share'
            # 可以在这里添加更多插件
        }
        
        # 检查插件是否存在
        if plugin_name not in plugin_log_files:
            return jsonify({'success': False, 'message': f'插件 {plugin_name} 不存在'}), 404
        
        # 日志文件路径
        log_dir = os.path.join(os.path.dirname(__file__), '..', '..', 'logs')
        # 获取当前日期的日志文件
        current_date = datetime.datetime.now().strftime('%Y-%m-%d')
        log_file_name = plugin_log_files[plugin_name]
        log_file = os.path.join(log_dir, 'plugins', log_file_name, f'{log_file_name}-{current_date}.log')
        
        # 读取日志内容
        if os.path.exists(log_file):
            with open(log_file, 'r', encoding='utf-8', errors='ignore') as f:
                logs = f.read()
        else:
            logs = f'{plugin_name} 插件尚未执行或日志文件不存在'
        
        return jsonify({'success': True, 'logs': logs})
    except Exception as e:
        logger.error(f"读取 {plugin_name} 插件日志时出错: {str(e)}")
        return jsonify({'success': False, 'message': str(e)}), 500

# SSE接口，用于实时推送插件日志
@plugins_bp.route('/<plugin_name>/logs/sse', methods=['GET'])
def get_plugin_logs_sse(plugin_name):
    try:
        # 从URL参数获取token
        from flask import request
        token = request.args.get('token')
        if not token:
            return "", 401
        
        # 验证token
        from utils.auth import verify_token
        try:
            success, payload = verify_token(token)
            if not success:
                return "", 401
            current_user = payload['username']
        except Exception as e:
            logger.error(f"验证SSE token时出错: {str(e)}")
            return "", 401
    except Exception as e:
        logger.error(f"SSE接口初始化时出错: {str(e)}")
        return "", 500
    
    try:
        # 插件日志文件映射
        plugin_log_files = {
            '189share': 'cloudpan189share'
            # 可以在这里添加更多插件
        }
        
        # 检查插件是否存在
        if plugin_name not in plugin_log_files:
            def generate_error():
                yield f"data: 插件 {plugin_name} 不存在\n\n"
            return Response(generate_error(), content_type='text/event-stream')
        
        # 日志文件路径
        log_dir = os.path.join(os.path.dirname(__file__), '..', '..', 'logs')
        # 获取当前日期的日志文件
        current_date = datetime.datetime.now().strftime('%Y-%m-%d')
        log_file_name = plugin_log_files[plugin_name]
        log_file = os.path.join(log_dir, 'plugins', log_file_name, f'{log_file_name}-{current_date}.log')
        
        # 确保日志文件存在
        if not os.path.exists(log_file):
            # 创建空日志文件
            os.makedirs(log_dir, exist_ok=True)
            with open(log_file, 'w', encoding='utf-8') as f:
                f.write('')
        
        def generate():
            # 读取文件的当前位置
            file_position = 0
            
            while True:
                try:
                    # 检查文件是否存在
                    if not os.path.exists(log_file):
                        yield f"data: 日志文件不存在\n\n"
                        time.sleep(1)
                        continue
                    
                    # 打开文件并读取新内容
                    with open(log_file, 'r', encoding='utf-8', errors='ignore') as f:
                        # 移动到上次读取的位置
                        f.seek(file_position)
                        # 读取新内容
                        new_content = f.read()
                        # 更新文件位置
                        file_position = f.tell()
                    
                    # 如果有新内容，发送到客户端
                    if new_content:
                        # 按照SSE格式发送数据，每个数据块以data:开头，以\n\n结尾
                        # 对于多行内容，每行都需要以data:开头
                        lines = new_content.strip().split('\n')
                        for line in lines:
                            yield f"data: {line}\n"
                        yield "\n"
                    
                    # 休眠1秒，避免过于频繁的文件读取
                    time.sleep(1)
                except Exception as e:
                    logger.error(f"[{plugin_name}] SSE推送日志时出错: {str(e)}")
                    yield f"data: 推送日志时出错: {str(e)}\n\n"
                    time.sleep(1)
        
        # 返回SSE响应
        return Response(generate(), content_type='text/event-stream')
    except Exception as e:
        logger.error(f"SSE接口执行时出错: {str(e)}")
        return "", 500

# 中断插件脚本执行
@plugins_bp.route('/<plugin_name>/stop', methods=['POST'])
@token_required
def stop_plugin(current_user, plugin_name):
    try:
        # 检查插件是否存在于进程字典中
        if plugin_name in script_processes:
            # 获取进程对象
            process = script_processes[plugin_name]
            # 终止进程
            process.terminate()
            try:
                # 等待进程终止
                process.wait(timeout=5)
            except subprocess.TimeoutExpired:
                # 如果进程在5秒内没有终止，强制杀死
                process.kill()
            # 从字典中移除进程
            del script_processes[plugin_name]
            logger.info(f"[{plugin_name}] 插件脚本已成功中断")
            return jsonify({'success': True, 'message': f'{plugin_name} 插件脚本已成功中断'})
        else:
            logger.info(f"[{plugin_name}] 没有正在执行的插件脚本，无需中断")
            return jsonify({'success': False, 'message': f'没有正在执行的 {plugin_name} 插件脚本'})
    except KeyError as e:
        logger.info(f"[{plugin_name}] 插件脚本进程不存在，可能已经执行完成")
        return jsonify({'success': False, 'message': f'{plugin_name} 插件脚本进程不存在，可能已经执行完成'})
    except Exception as e:
        logger.error(f"中断 {plugin_name} 插件脚本时出错: {str(e)}")
        return jsonify({'success': False, 'message': str(e)}), 500
