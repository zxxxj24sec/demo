"""
用户管理路由模块
处理用户列表、详情、编辑、删除等用户管理请求
"""
from flask import request, session, render_template
from services.user_service import UserService


def register_user_routes(app):
    """
    注册用户管理相关路由
    :param app: Flask 应用实例
    """

    @app.route("/users")
    def users():
        """用户列表路由"""
        # 检查用户是否已登录
        if "user" not in session:
            return render_template("login.html", success=False, message="请先登录")

        # 获取当前登录用户信息
        current_user = session["user"]
        current_is_admin = session.get("is_admin", False)

        # 调用用户服务获取所有用户列表
        users_list = UserService.get_all_users()

        return render_template(
            "users.html",
            users=users_list,
            current_user=current_user,
            is_admin=current_is_admin
        )

    @app.route("/user/<int:user_id>", methods=["GET", "POST"])
    def user_detail(user_id):
        """用户详情/编辑路由"""
        # 检查用户是否已登录
        if "user" not in session:
            return render_template("login.html", success=False, message="请先登录")

        # 获取当前登录用户信息
        current_user = session["user"]
        current_is_admin = session.get("is_admin", False)

        # 调用用户服务获取目标用户信息
        user = UserService.get_user_by_id(user_id)

        # 如果用户不存在，返回错误信息
        if not user:
            return render_template("user_detail.html", user=None, success=False, message="用户不存在")

        # 权限检查：只有管理员或用户本人才能查看详情
        if not current_is_admin and current_user != user["username"]:
            return render_template(
                "user_detail.html",
                user=None,
                success=False,
                message="权限不足：只能查看自己的用户详情"
            )

        # 处理 POST 请求（编辑用户）
        if request.method == "POST":
            # 权限检查：只有管理员才能编辑用户
            if not current_is_admin:
                return render_template(
                    "user_detail.html",
                    user={"id": user_id, "username": user["username"]},
                    success=False,
                    message="权限不足：只有管理员才能编辑用户"
                )

            # 获取表单提交的数据
            new_username = request.form.get("username")
            new_password = request.form.get("password")
            new_gender = request.form.get("gender")
            new_email = request.form.get("email")

            try:
                # 调用用户服务更新用户信息
                updated_user = UserService.update_user(
                    user_id,
                    username=new_username,
                    password=new_password,
                    gender=new_gender,
                    email=new_email
                )
                return render_template(
                    "user_detail.html",
                    user=updated_user,
                    success=True,
                    message="更新成功",
                    is_admin=current_is_admin
                )
            except Exception as e:
                return render_template(
                    "user_detail.html",
                    user=user,
                    success=False,
                    message=f"更新失败：{str(e)}",
                    is_admin=current_is_admin
                )
        else:
            # GET 请求：显示用户详情
            return render_template(
                "user_detail.html",
                user=user,
                success=True,
                is_admin=current_is_admin
            )

    @app.route("/user/delete/<int:user_id>")
    def delete_user(user_id):
        """删除用户路由"""
        # 检查用户是否已登录
        if "user" not in session:
            return render_template("login.html", success=False, message="请先登录")

        # 权限检查：只有管理员才能删除用户
        if not session.get("is_admin", False):
            return render_template(
                "users.html",
                users=None,
                success=False,
                message="权限不足：只有管理员才能删除用户",
                current_user=session["user"],
                is_admin=False
            )

        try:
            # 调用用户服务删除用户
            UserService.delete_user(user_id)
            # 删除成功后重新获取用户列表
            users_list = UserService.get_all_users()
            return render_template(
                "users.html",
                users=users_list,
                success=True,
                message="删除成功",
                current_user=session["user"],
                is_admin=True
            )
        except Exception as e:
            return render_template(
                "users.html",
                users=None,
                success=False,
                message=f"删除失败：{str(e)}",
                current_user=session["user"],
                is_admin=True
            )