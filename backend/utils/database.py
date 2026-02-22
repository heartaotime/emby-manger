import pymysql
from config.database import db_config

def get_db_connection():
    """
    获取数据库连接
    :return: 数据库连接对象
    """
    return pymysql.connect(**db_config)

def init_db():
    """
    初始化数据库
    :return: None
    """
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
