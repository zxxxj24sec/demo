"""
Flask 应用主入口文件
负责初始化应用、配置路由等
"""
from flask import Flask, render_template

# 创建 Flask 应用实例
app = Flask(__name__)

# Session 加密密钥
app.secret_key = "test1234"


@app.route("/")
def index():
    """首页路由"""
    return render_template("index.html")


# 注册路由模块
from routes.auth import register_auth_routes
from routes.profile import register_profile_routes
from routes.user import register_user_routes
from routes.announcement import register_announcement_routes

register_auth_routes(app)
register_profile_routes(app)
register_user_routes(app)
register_announcement_routes(app)


if __name__ == "__main__":
    # 启动应用，允许外部访问
    app.run(debug=True, host='0.0.0.0')