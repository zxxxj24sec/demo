"""
个人主页路由模块
处理个人主页相关请求，包括头像上传功能
"""
import os
import uuid
import imghdr  # 导入图片类型检测模块
from flask import session, render_template, request, redirect, url_for
from services.user_service import UserService


def register_profile_routes(app):
    """
    注册个人主页相关路由
    :param app: Flask 应用实例
    """

    @app.route("/profile", methods=["GET", "POST"])
    def profile():
        """个人主页路由"""
        if "user" not in session:
            return render_template("profile.html", logged_in=False)

        # 获取当前用户信息
        user_info = UserService.get_user_by_username(session["user"])
        
        # 处理头像上传
        if request.method == "POST" and "avatar" in request.files:
            file = request.files["avatar"]
            if file.filename != "":
                # 验证文件类型（扩展名检查）
                allowed_extensions = {'png', 'jpg', 'jpeg', 'gif'}
                # 从文件名中提取扩展名（如 .jpg），转换为小写；如果文件名不含点则返回空字符串
                extension = file.filename.rsplit('.', 1)[1].lower() if '.' in file.filename else ''
                
                if extension in allowed_extensions:
                    # 使用 imghdr 检测文件真实类型（防止恶意文件伪装成图片）
                    file.seek(0)  # 确保文件指针在开头
                    real_type = imghdr.what(file)
                    file.seek(0)  # 重置文件指针供后续保存使用
                    
                    # 验证文件真实类型是否为允许的图片格式
                    if real_type not in ['png', 'jpg', 'jpeg', 'gif']:
                        return render_template(
                            "profile.html",
                            logged_in=True,
                            username=session["user"],
                            is_admin=session.get("is_admin", False),
                            gender=session.get("gender", ""),
                            email=session.get("email", ""),
                            avatar=session.get("avatar", ""),
                            error_message="非法图片文件：文件内容与扩展名不一致"
                        )
                    
                    # 生成唯一文件名
                    filename = str(uuid.uuid4()) + '.' + extension
                    # 确保上传目录存在
                    upload_dir = os.path.join(app.root_path, 'static', 'avatars')
                    os.makedirs(upload_dir, exist_ok=True)
                    # 保存文件
                    file.save(os.path.join(upload_dir, filename))
                    
                    # 更新用户头像信息
                    try:
                        UserService.update_user(user_info['id'], avatar=filename)
                        # 更新session中的头像信息
                        session['avatar'] = filename
                        return redirect(url_for('profile'))
                    except Exception as e:
                        return render_template(
                            "profile.html",
                            logged_in=True,
                            username=session["user"],
                            is_admin=session.get("is_admin", False),
                            gender=session.get("gender", ""),
                            email=session.get("email", ""),
                            avatar=session.get("avatar", ""),
                            error_message=f"头像上传失败：{str(e)}"
                        )
                else:
                    return render_template(
                        "profile.html",
                        logged_in=True,
                        username=session["user"],
                        is_admin=session.get("is_admin", False),
                        gender=session.get("gender", ""),
                        email=session.get("email", ""),
                        avatar=session.get("avatar", ""),
                        error_message="只支持 png、jpg、jpeg、gif 格式的图片"
                    )

        # 获取头像信息
        avatar = user_info.get('avatar', '') if user_info else ''
        session['avatar'] = avatar

        return render_template(
            "profile.html",
            logged_in=True,
            username=session["user"],
            is_admin=session.get("is_admin", False),
            gender=session.get("gender", ""),
            email=session.get("email", ""),
            avatar=avatar
        )