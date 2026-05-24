"""
公告路由模块
处理公告列表、详情、发布、评论等请求
"""
from flask import request, session, render_template, redirect, url_for
from services.announcement_service import AnnouncementService
from services.user_service import UserService


def register_announcement_routes(app):
    """
    注册公告相关路由
    :param app: Flask 应用实例
    """

    @app.route("/announcements")
    def announcements():
        """公告列表页"""
        page = int(request.args.get("page", 1))
        per_page = 10

        announcements_list = AnnouncementService.get_all_announcements(page, per_page)
        total_count = AnnouncementService.get_total_count()
        total_pages = (total_count + per_page - 1) // per_page

        return render_template(
            "announcements.html",
            announcements=announcements_list,
            current_page=page,
            total_pages=total_pages
        )

    @app.route("/announcement/<int:announcement_id>")
    def announcement_detail(announcement_id):
        """公告详情页"""
        announcement = AnnouncementService.get_announcement_by_id(announcement_id)
        if not announcement:
            return render_template("announcement_detail.html", error="公告不存在")

        comments = AnnouncementService.get_comments_by_announcement(announcement_id)

        return render_template(
            "announcement_detail.html",
            announcement=announcement,
            comments=comments
        )

    @app.route("/announcement/create", methods=["GET", "POST"])
    def create_announcement():
        """创建公告页"""
        # 检查是否已登录
        if "user" not in session:
            return redirect(url_for("index"))

        if request.method == "POST":
            title = request.form.get("title")
            content = request.form.get("content")

            if not title or not content:
                return render_template(
                    "create_announcement.html",
                    error="标题和内容不能为空"
                )

            try:
                user = UserService.get_user_by_username(session["user"])
                AnnouncementService.create_announcement(
                    title=title,
                    content=content,
                    author_id=user["id"],
                    author_name=user["username"]
                )
                return redirect(url_for("announcements"))
            except Exception as e:
                return render_template(
                    "create_announcement.html",
                    error=f"创建公告失败：{str(e)}"
                )

        return render_template("create_announcement.html")

    @app.route("/announcement/<int:announcement_id>/delete", methods=["POST"])
    def delete_announcement(announcement_id):
        """删除公告"""
        # 检查是否已登录且是管理员
        if "user" not in session or not session.get("is_admin"):
            return redirect(url_for("announcements"))

        try:
            AnnouncementService.delete_announcement(announcement_id)
        except Exception as e:
            print(f"删除公告失败：{str(e)}")

        return redirect(url_for("announcements"))

    @app.route("/announcement/<int:announcement_id>/comment", methods=["POST"])
    def add_comment(announcement_id):
        """添加评论"""
        # 检查是否已登录
        if "user" not in session:
            return redirect(url_for("announcement_detail", announcement_id=announcement_id))

        content = request.form.get("content")
        if not content:
            return redirect(url_for("announcement_detail", announcement_id=announcement_id))

        try:
            user = UserService.get_user_by_username(session["user"])
            AnnouncementService.add_comment(
                announcement_id=announcement_id,
                user_id=user["id"],
                username=user["username"],
                content=content
            )
        except Exception as e:
            print(f"添加评论失败：{str(e)}")

        return redirect(url_for("announcement_detail", announcement_id=announcement_id))

    @app.route("/announcement/<int:announcement_id>/comment/<int:comment_id>/delete", methods=["POST"])
    def delete_comment(announcement_id, comment_id):
        """删除评论"""
        # 检查是否已登录
        if "user" not in session:
            return redirect(url_for("announcement_detail", announcement_id=announcement_id))

        # 只有评论作者或管理员可以删除
        comments = AnnouncementService.get_comments_by_announcement(announcement_id)
        comment_to_delete = None
        for comment in comments:
            if comment["id"] == comment_id:
                comment_to_delete = comment
                break

        if not comment_to_delete:
            return redirect(url_for("announcement_detail", announcement_id=announcement_id))

        # 检查是否有权限删除（评论作者或管理员）
        user = UserService.get_user_by_username(session["user"])
        if comment_to_delete["user_id"] != user["id"] and not session.get("is_admin"):
            return redirect(url_for("announcement_detail", announcement_id=announcement_id))

        try:
            AnnouncementService.delete_comment(comment_id)
        except Exception as e:
            print(f"删除评论失败：{str(e)}")

        return redirect(url_for("announcement_detail", announcement_id=announcement_id))
