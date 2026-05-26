"""
API 模块初始化文件
"""
from flask import Blueprint

# 创建 API Blueprint
api_bp = Blueprint('api', __name__, url_prefix='/api')

# 导入各个 API 路由模块
from api.auth import register_auth_api
from api.user import register_user_api
from api.course import register_course_api
from api.announcement import register_announcement_api