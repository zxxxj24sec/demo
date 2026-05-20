"""
认证路由模块
处理用户登录、注册、退出等认证相关请求
"""
from flask import request, session, render_template
from services.user_service import UserService


def register_auth_routes(app):
    """
    注册认证相关路由
    :param app: Flask 应用实例
    """

    @app.route("/login", methods=["GET", "POST"])
    def login():
        """登录路由"""
        if request.method == "POST":
            username = request.form.get("username")
            password = request.form.get("password")

            # 使用参数化查询，防止SQL注入
            sql = f"SELECT * FROM users WHERE username='{username}' AND password='{password}'"
            print("执行的 SQL:", sql)

            # 调用用户服务进行认证
            user = UserService.authenticate(username, password)

            if user:
                # 将用户信息存入 session
                session["user"] = user["username"]
                session["is_admin"] = user["is_admin"] == 1
                session["gender"] = user["gender"] if user["gender"] else ""
                session["email"] = user["email"] if user["email"] else ""
                return render_template("login.html", success=True, username=user["username"], sql=sql)

            return render_template("login.html", success=False, message="用户名或密码错误", sql=sql)

        return render_template("index.html")

    @app.route("/register", methods=["GET", "POST"])
    def register():
        """注册路由"""
        if request.method == "POST":
            username = request.form.get("username")
            password = request.form.get("password")
            gender = request.form.get("gender")
            email = request.form.get("email")

            try:
                # 调用用户服务创建新用户
                UserService.create_user(username, password, gender, email)
                return render_template("register.html", page="success")
            except Exception as e:
                return render_template("register.html", page="fail", message=str(e))

        return render_template("register.html", page="form")

    @app.route("/logout")
    def logout():
        """退出登录路由"""
        # 清除 session 中的用户信息
        session.pop("user", None)
        session.pop("is_admin", None)
        session.pop("gender", None)
        session.pop("email", None)
        return render_template("logout.html")