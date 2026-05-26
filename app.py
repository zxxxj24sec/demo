"""
Flask 应用主入口文件
负责初始化应用、配置路由等
"""
from flask import Flask, render_template, jsonify, request
from flask_cors import CORS

# 创建 Flask 应用实例
app = Flask(__name__)

# Session 加密密钥
app.secret_key = "test1234"

# ============================================
# CORS 安全漏洞配置 - 故意留下的漏洞！
# ============================================

# 漏洞1: 允许所有来源（生产环境中极少见，但测试环境常见）
# 攻击者可以从任意网站读取 API 返回的数据
CORS(app, resources={r"/api/*": {"origins": "*"}})

# 漏洞2: 允许携带认证信息（credentials）
# 结合上面的 origins: *，会导致严重的安全问题
# 如果在响应头中设置了 Authorization: Bearer xxx
# 恶意网站可以窃取用户的 token

# 漏洞3: 允许所有 HTTP 方法
# 恶意网站可以执行 DELETE、PUT 等危险操作


@app.route("/")
def index():
    """首页路由"""
    return render_template("index.html")


@app.route("/api")
def api_index():
    """API 首页"""
    return jsonify({
        "msg": "欢迎使用学校管理系统 API",
        "version": "1.0",
        "endpoints": {
            "认证相关": {
                "POST /api/login": "用户登录",
                "POST /api/register": "用户注册",
                "GET /api/me": "获取当前用户信息",
                "POST /api/logout": "退出登录",
                "GET /api/verify": "验证 Token"
            },
            "用户管理": {
                "GET /api/users": "获取所有用户（漏洞：无权限控制）",
                "GET /api/user/<id>": "获取用户详情（漏洞：IDOR）",
                "PUT /api/user/<id>": "更新用户（漏洞：水平权限绕过）",
                "DELETE /api/user/<id>": "删除用户（漏洞：未授权）"
            },
            "课程管理": {
                "GET /api/courses": "获取课程列表",
                "GET /api/course/<id>": "获取课程详情",
                "GET /api/course/<id>/grade": "获取成绩（漏洞：参数篡改）",
                "POST /api/course/<id>/enroll": "选课"
            },
            "公告管理": {
                "GET /api/announcements": "获取公告列表",
                "GET /api/announcement/<id>": "获取公告详情",
                "POST /api/announcement/<id>/comment": "添加评论（漏洞：存储型XSS）",
                "GET /api/announcement/search": "搜索公告（漏洞：SQL注入）"
            },
            "JWT 漏洞演示": {
                "GET /api/jwt/none": "演示 none 算法漏洞",
                "POST /api/jwt/crack": "模拟 JWT 密钥爆破"
            }
        },
        "warning": "本系统仅供学习安全测试使用，请勿用于非法用途！"
    })


# ============================================
# CORS 漏洞演示接口
# ============================================
@app.route("/api/cors-test", methods=["GET", "POST", "PUT", "DELETE"])
def api_cors_test():
    """
    CORS 漏洞演示接口

    漏洞配置:
    1. Access-Control-Allow-Origin: * （允许所有来源）
    2. Access-Control-Allow-Credentials: true （允许携带认证信息）

    攻击场景:
    恶意网站 http://evil.com 可以:
    1. 使用受害者的身份（携带 cookie/token）请求此接口
    2. 读取接口返回的敏感数据

    测试方法:
    在浏览器控制台执行:
    fetch('http://localhost:5000/api/cors-test', {
        method: 'GET',
        credentials: 'include'  // 携带认证信息
    }).then(r => r.json()).then(console.log)
    """
    return jsonify({
        "msg": "这是一个存在 CORS 漏洞的接口",
        "your_ip": request.remote_addr,
        "headers": dict(request.headers),
        "warning": "恶意网站可以利用此接口获取你的敏感信息"
    })


# ============================================
# 故意泄露敏感信息的接口
# ============================================
@app.route("/api/debug/info", methods=["GET"])
def api_debug_info():
    """
    调试信息泄露漏洞

    生产环境不应该暴露此类接口
    可能泄露: 服务器路径、Python版本、已安装包等
    """
    import sys
    import os

    return jsonify({
        "python_version": sys.version,
        "platform": sys.platform,
        "cwd": os.getcwd(),
        "env_vars": {
            "PATH": os.environ.get("PATH", "")[:100] + "...",
            "USER": os.environ.get("USER", "unknown"),
        },
        "flask_version": "2.0.0",  # 简化
        "warning": "这是敏感信息，生产环境切勿暴露！"
    })


# 注册原有的路由模块（保留前端页面）
from routes.auth import register_auth_routes
from routes.profile import register_profile_routes
from routes.user import register_user_routes
from routes.announcement import register_announcement_routes

register_auth_routes(app)
register_profile_routes(app)
register_user_routes(app)
register_announcement_routes(app)

# 注册 API 路由
from api import api_bp
app.register_blueprint(api_bp)


if __name__ == "__main__":
    print("=" * 60)
    print("学校管理系统 API 学习平台")
    print("=" * 60)
    print("启动地址: http://localhost:5000")
    print("API 文档: http://localhost:5000/api")
    print("")
    print("已启用的安全漏洞（用于学习）:")
    print("  1. JWT 弱密钥 (secret123)")
    print("  2. JWT none 算法支持")
    print("  3. IDOR 越权访问")
    print("  4. CORS 配置错误")
    print("  5. SQL 注入风险")
    print("  6. 存储型 XSS")
    print("  7. 未授权访问")
    print("  8. 敏感数据泄露")
    print("=" * 60)
    print("")
    # 启动应用，允许外部访问
    app.run(debug=True, host='0.0.0.0')