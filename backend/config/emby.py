import os

# Emby 配置
emby_config = {
    'url': os.getenv('EMBY_URL', 'http://localhost:8096'),
    'api_key': os.getenv('EMBY_API_KEY', ''),
    'template_user_id': os.getenv('EMBY_TEMPLATE_USER_ID', '')
}
