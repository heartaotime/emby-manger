import os

# JWT配置
SECRET_KEY = os.getenv('SECRET_KEY', 'your-secret-key-here')
ADMIN_USERNAME = os.getenv('ADMIN_USERNAME', 'admin')
ADMIN_PASSWORD = os.getenv('ADMIN_PASSWORD', 'admin123')
