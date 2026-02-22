import os
import sqlite3
import requests
import json
import urllib.parse
from datetime import datetime
from dotenv import load_dotenv
import time
import re
import pandas as pd
import random

# 加载环境变量
load_dotenv()

# 确保data目录存在
if not os.path.exists('data'):
    os.makedirs('data')

# 从环境变量获取配置
MP_API_URL = os.getenv('189SHARE_MP_API_URL')
MP_API_TOKEN = os.getenv('189SHARE_MP_API_TOKEN')
ID_START = int(os.getenv('189SHARE_ID_START', '0'))
DB_PATH = os.getenv('189SHARE_DB_PATH')
DIRECT_UPDATE = os.getenv('189SHARE_DIRECT_UPDATE', 'false').lower() == 'true'

# 检查环境变量是否存在
if not MP_API_URL:
    raise ValueError("189SHARE_MP_API_URL 环境变量未设置")
if not MP_API_TOKEN:
    raise ValueError("189SHARE_MP_API_TOKEN 环境变量未设置")
if not DB_PATH:
    raise ValueError("189SHARE_DB_PATH 环境变量未设置")

# 连接到数据库
conn = sqlite3.connect(DB_PATH)
cursor = conn.cursor()



# 使用新的API接口获取媒体信息
def get_media_info(name):
    # 对名称进行 URL 编码
    encoded_title = urllib.parse.quote(name)
    
    # 构建 API 请求 URL
    url = f"{MP_API_URL}?token={MP_API_TOKEN}&title={encoded_title}&subtitle="
    
    
    # 发送请求
    try:
        response = requests.get(url, headers={}, verify=False, timeout=30)
        response.raise_for_status()
        return response.json()
    except requests.RequestException as e:
        print(f"API请求错误: {str(e)}")
        return {}
    except json.JSONDecodeError as e:
        print(f"解析API响应错误: {str(e)}")
        return {}

# 判断剧集是否还在更新
def is_show_still_running(media_info):
    media_info_data = media_info.get('media_info', {})
    if media_info_data is None:
        media_info_data = {}
    status = media_info_data.get('status', '')
    return status == 'Returning Series'

# 获取总记录数
cursor.execute('SELECT COUNT(*) FROM mount_points WHERE id > ?', (ID_START,))
total_records = cursor.fetchone()[0]
print(f"总记录数 (id > {ID_START}): {total_records}")

# 分页查询参数
page_size = 100  # 每页处理100条记录
current_record = 0

# 处理每个记录
running_shows = []

# 分页查询并处理
while current_record < total_records:
    # 计算偏移量
    offset = current_record
    # 执行分页查询，按id升序排列
    cursor.execute('SELECT id, name FROM mount_points WHERE id > ? ORDER BY id ASC LIMIT ? OFFSET ?', (ID_START, page_size, offset))
    batch_records = cursor.fetchall()
    
    # 处理当前批次的记录
    for record in batch_records:
        current_record += 1
        id_, name = record
        print(f"\n=== 处理第 {current_record}/{total_records} 个: {name} ===")
        
        try:
            # 获取媒体信息
            media_info = get_media_info(name)
            if media_info:
                # print(f"API响应: {json.dumps(media_info, ensure_ascii=False)[:200]}...")
                try:
                    # 提取识别后的名称和年份
                    meta_info = media_info.get('meta_info', {})
                    if meta_info is None:
                        meta_info = {}
                    recognized_name = meta_info.get('name', name) if meta_info else name
                    year = meta_info.get('year', '') if meta_info else ''
                    
                    # 提取状态信息
                    media_info_data = media_info.get('media_info', {})
                    if media_info_data is None:
                        media_info_data = {}
                    status = media_info_data.get('status', '') if media_info_data else ''
                    
                    # 判断是否在更新
                    if is_show_still_running(media_info):
                        # 生成refresh_interval并保持一致
                        refresh_interval = random.choice(list(range(30, 241, 5)))
                        show_info = {
                            'id': id_,
                            'original_name': name,
                            'name': recognized_name,
                            'year': year,
                            'status': status,
                            'refresh_interval': refresh_interval
                        }
                        running_shows.append(show_info)
                        print(f"✓ {name} 正在更新中")
                        print(f"  识别名称: {recognized_name}")
                        print(f"  识别年份: {year}")
                        print(f"  更新状态: {status}")
                        print(f"  刷新间隔: {refresh_interval}分钟")
                        
                        # 实时写入Excel文件
                        excel_file = 'data/需要追更的剧集.xlsx'
                        # 准备当前数据
                        excel_data = []
                        for show in running_shows:
                            excel_data.append({
                                'ID': show['id'],
                                '原始名称': show['original_name'],
                                '识别名称': show['name'],
                                '识别年份': show['year'],
                                '刷新间隔': show['refresh_interval']
                            })
                        # 创建DataFrame并写入
                        try:
                            df = pd.DataFrame(excel_data)
                            df.to_excel(excel_file, index=False)
                            print(f"  已将 {name} 写入Excel文件")
                        except Exception as e:
                            print(f"  写入Excel文件失败: {str(e)}")
                        
                        # 实时更新SQL文件
                        sql_file = 'data/auto_refresh_update.sql'
                        try:
                            with open(sql_file, 'w', encoding='utf-8') as f:
                                f.write('-- 自动刷新设置更新SQL\n')
                                f.write('-- 更新需要追更的剧集的自动刷新设置\n\n')
                                for show in running_shows:
                                    show_id = show['id']
                                    show_refresh_interval = show['refresh_interval']
                                    sql = f"UPDATE mount_points SET enable_auto_refresh = 1, auto_refresh_days = 365, auto_refresh_begin_at = '2026-01-01 00:00:00', refresh_interval = {show_refresh_interval} WHERE id = {show_id};\n"
                                    f.write(sql)
                            print(f"  已更新SQL文件: {sql_file}")
                        except Exception as e:
                            print(f"  更新SQL文件失败: {str(e)}")
                        
                        # 如果启用直接更新，只更新当前剧集
                        if DIRECT_UPDATE:
                            try:
                                sql = f"UPDATE mount_points SET enable_auto_refresh = 1, auto_refresh_days = 365, auto_refresh_begin_at = '2026-01-01 00:00:00', refresh_interval = {refresh_interval} WHERE id = {id_};"
                                cursor.execute(sql)
                                conn.commit()
                                print(f"  已直接更新数据库: ID={id_}")
                            except Exception as e:
                                print(f"  直接更新数据库失败: {str(e)}")
                                conn.rollback()
                    else:
                        print(f"✗ {name} 未在更新中")
                        print(f"  识别名称: {recognized_name}")
                        print(f"  识别年份: {year}")
                        print(f"  更新状态: {status}")
                except Exception as e:
                    print(f"✗ 处理识别信息时出错: {str(e)}")
                    print(f"  原始名称: {name}")
            else:
                print(f"✗ 无法获取媒体信息: {name}")
        except Exception as e:
            print(f"✗ 处理 {name} 时出错: {str(e)}")

# 输出结果
print("\n=== 正在更新的剧集列表 ===")
for show in running_shows:
    print(f"ID: {show['id']}")
    print(f"名称: {show['name']}")
    print(f"原始名称: {show['original_name']}")
    print(f"状态: {show['status']}")
    print()

# 检查是否有需要追更的剧集
if running_shows:
    print(f"\n已将需要追更的剧集信息实时保存到: data/需要追更的剧集.xlsx")
    
    # 生成SQL更新文件
    sql_file = 'data/auto_refresh_update.sql'
    try:
        with open(sql_file, 'w', encoding='utf-8') as f:
            f.write('-- 自动刷新设置更新SQL\n')
            f.write('-- 更新需要追更的剧集的自动刷新设置\n\n')
            for show in running_shows:
                show_id = show['id']
                show_refresh_interval = show['refresh_interval']
                sql = f"UPDATE mount_points SET enable_auto_refresh = true, auto_refresh_days = 365, auto_refresh_begin_at = '2000-01-01 00:00:00', refresh_interval = {show_refresh_interval} WHERE id = {show_id};\n"
                f.write(sql)
            print(f"\n已生成SQL更新文件: {sql_file}")
    except Exception as e:
        print(f"生成SQL文件失败: {str(e)}")
else:
    print("\n没有需要追更的剧集")
    # 如果没有需要追更的剧集，创建一个空的Excel文件
    excel_file = 'data/需要追更的剧集.xlsx'
    try:
        df = pd.DataFrame(columns=['ID', '原始名称', '识别名称', '识别年份'])
        df.to_excel(excel_file, index=False)
        print(f"已创建空的Excel文件: {excel_file}")
    except Exception as e:
        print(f"创建空Excel文件失败: {str(e)}")

# 关闭数据库连接
conn.close()