"""
公告服务模块
处理公告的发布、查询、评论等业务逻辑
"""
from utils.db import execute_query, execute_one, execute_update
from datetime import datetime


class AnnouncementService:
    """
    公告服务类
    提供公告相关的业务操作方法
    """

    @staticmethod
    def get_all_announcements(page=1, per_page=10):
        """
        获取所有公告列表（分页）
        :param page: 页码
        :param per_page: 每页数量
        :return: 公告列表
        """
        offset = (page - 1) * per_page
        # 置顶公告排在前面
        sql = """
            SELECT * FROM announcements
            ORDER BY is_top DESC, created_at DESC
            LIMIT %s OFFSET %s
        """
        return execute_query(sql, (per_page, offset))

    @staticmethod
    def get_announcement_by_id(announcement_id):
        """
        根据ID获取公告详情
        :param announcement_id: 公告ID
        :return: 公告信息
        """
        # 增加浏览次数
        update_sql = "UPDATE announcements SET view_count = view_count + 1 WHERE id = %s"
        execute_update(update_sql, (announcement_id,))

        sql = "SELECT * FROM announcements WHERE id = %s"
        return execute_one(sql, (announcement_id,))

    @staticmethod
    def create_announcement(title, content, author_id, author_name):
        """
        创建新公告
        :param title: 标题
        :param content: 内容
        :param author_id: 作者ID
        :param author_name: 作者用户名
        :return: 新公告ID
        """
        sql = """
            INSERT INTO announcements (title, content, author_id, author_name)
            VALUES (%s, %s, %s, %s)
        """
        execute_update(sql, (title, content, author_id, author_name))

        # 获取新插入公告的ID
        result = execute_one(
            "SELECT id FROM announcements ORDER BY id DESC LIMIT 1"
        )
        return result['id'] if result else None

    @staticmethod
    def update_announcement(announcement_id, title=None, content=None, is_top=None):
        """
        更新公告
        :param announcement_id: 公告ID
        :param title: 标题（可选）
        :param content: 内容（可选）
        :param is_top: 是否置顶（可选）
        :return: 更新后的公告
        """
        update_fields = []
        params = []

        if title:
            update_fields.append("title = %s")
            params.append(title)
        if content:
            update_fields.append("content = %s")
            params.append(content)
        if is_top is not None:
            update_fields.append("is_top = %s")
            params.append(is_top)

        if not update_fields:
            return AnnouncementService.get_announcement_by_id(announcement_id)

        params.append(announcement_id)
        sql = f"UPDATE announcements SET {', '.join(update_fields)} WHERE id = %s"
        execute_update(sql, params)

        return AnnouncementService.get_announcement_by_id(announcement_id)

    @staticmethod
    def delete_announcement(announcement_id):
        """
        删除公告（同时删除关联的评论）
        :param announcement_id: 公告ID
        :return: 是否删除成功
        """
        # 先删除关联的评论
        delete_comments_sql = "DELETE FROM announcement_comments WHERE announcement_id = %s"
        execute_update(delete_comments_sql, (announcement_id,))

        # 删除公告
        delete_sql = "DELETE FROM announcements WHERE id = %s"
        rowcount = execute_update(delete_sql, (announcement_id,))
        return rowcount > 0

    @staticmethod
    def get_comments_by_announcement(announcement_id):
        """
        获取公告的所有评论
        :param announcement_id: 公告ID
        :return: 评论列表
        """
        sql = """
            SELECT * FROM announcement_comments
            WHERE announcement_id = %s
            ORDER BY created_at ASC
        """
        return execute_query(sql, (announcement_id,))

    @staticmethod
    def add_comment(announcement_id, user_id, username, content):
        """
        添加评论
        :param announcement_id: 公告ID
        :param user_id: 用户ID
        :param username: 用户名
        :param content: 评论内容
        :return: 新评论ID
        """
        sql = """
            INSERT INTO announcement_comments (announcement_id, user_id, username, content)
            VALUES (%s, %s, %s, %s)
        """
        execute_update(sql, (announcement_id, user_id, username, content))

        # 获取新评论ID
        result = execute_one(
            "SELECT id FROM announcement_comments ORDER BY id DESC LIMIT 1"
        )
        return result['id'] if result else None

    @staticmethod
    def delete_comment(comment_id):
        """
        删除评论
        :param comment_id: 评论ID
        :return: 是否删除成功
        """
        sql = "DELETE FROM announcement_comments WHERE id = %s"
        rowcount = execute_update(sql, (comment_id,))
        return rowcount > 0

    @staticmethod
    def get_total_count():
        """
        获取公告总数
        :return: 公告数量
        """
        sql = "SELECT COUNT(*) as count FROM announcements"
        result = execute_one(sql)
        return result['count'] if result else 0
