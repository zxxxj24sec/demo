"""
API 公告管理模块
包含公告列表、详情、评论等功能
设计了一些安全漏洞用于学习：
1. 存储型 XSS（已在模板层开启）
2. SQL 注入（可能存在）
3. 敏感数据泄露
"""
from flask import request, jsonify
from api import api_bp
from services.announcement_service import AnnouncementService
from services.user_service import UserService

# 导入数据库工具（可能存在 SQL 注入）
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from utils.db import execute_query, execute_one


def register_announcement_api(app):
    """
    注册 API 公告管理路由
    """

    # ============================================
    # 获取公告列表 API
    # ============================================
    @api_bp.route("/announcements", methods=["GET"])
    def api_get_announcements():
        """
        获取公告列表

        返回:
        {
            "announcements": [...]
        }
        """
        try:
            announcements = AnnouncementService.get_all_announcements()
            return jsonify({"announcements": announcements})
        except Exception as e:
            return jsonify({"msg": f"获取公告列表失败: {str(e)}"}), 500

    # ============================================
    # 获取指定公告详情 API
    # ============================================
    @api_bp.route("/announcement/<int:announcement_id>", methods=["GET"])
    def api_get_announcement(announcement_id):
        """
        获取指定公告详情
        """
        try:
            announcement = AnnouncementService.get_announcement_by_id(announcement_id)
            if not announcement:
                return jsonify({"msg": "公告不存在"}), 404

            return jsonify({"announcement": announcement})
        except Exception as e:
            return jsonify({"msg": f"获取公告详情失败: {str(e)}"}), 500

    # ============================================
    # 获取公告评论 API
    # ============================================
    @api_bp.route("/announcement/<int:announcement_id>/comments", methods=["GET"])
    def api_get_comments(announcement_id):
        """
        获取公告的所有评论

        漏洞: 评论内容可能包含存储型 XSS 攻击代码
        前端如果直接渲染而不过滤，会被执行
        """
        try:
            comments = AnnouncementService.get_comments_by_announcement(announcement_id)
            return jsonify({"comments": comments})
        except Exception as e:
            return jsonify({"msg": f"获取评论失败: {str(e)}"}), 500

    # ============================================
    # 添加评论 API - 存储型 XSS 入口
    # ============================================
    @api_bp.route("/announcement/<int:announcement_id>/comment", methods=["POST"])
    def api_add_comment(announcement_id):
        """
        添加评论 - 存储型 XSS 漏洞入口

        请求体:
        {
            "content": "这是评论内容"
        }

        漏洞: 恶意用户可以提交 <script>alert(1)</script> 等 XSS 代码
        这些代码会被存储到数据库中
        当其他用户查看公告详情时，XSS 代码会被执行
        """
        try:
            # 这里简化了，应该从 token 中获取用户信息
            auth_header = request.headers.get("Authorization")
            if not auth_header:
                return jsonify({"msg": "未登录"}), 401

            data = request.get_json()
            if not data:
                return jsonify({"msg": "请求体不能为空"}), 400

            content = data.get("content")
            if not content:
                return jsonify({"msg": "评论内容不能为空"}), 400

            # 假设从 token 中获取用户信息（简化版）
            username = "test_user"  # 实际应该从 JWT 中解析

            # 添加评论
            comment_id = AnnouncementService.add_comment(
                announcement_id=announcement_id,
                user_id=1,  # 简化
                username=username,
                content=content  # 直接存储，未过滤 XSS
            )

            return jsonify({
                "msg": "评论成功",
                "comment_id": comment_id
            }), 201

        except Exception as e:
            return jsonify({"msg": f"添加评论失败: {str(e)}"}), 500

    # ============================================
    # 搜索公告 API - 可能存在 SQL 注入
    # ============================================
    @api_bp.route("/announcement/search", methods=["GET"])
    def api_search_announcements():
        """
        搜索公告 - SQL 注入漏洞演示

        请求参数:
        ?keyword=test

        漏洞: 直接拼接 SQL，没有参数化查询
        可以注入: ?keyword=' OR 1=1 --
        """
        keyword = request.args.get("keyword", "")

        if not keyword:
            return jsonify({"announcements": []})

        # 故意使用字符串拼接（漏洞）
        sql = f"SELECT * FROM announcements WHERE title LIKE '%{keyword}%' OR content LIKE '%{keyword}%'"

        try:
            # 执行原始 SQL（仅用于演示，生产环境绝对不要这样做）
            results = execute_query(sql)
            return jsonify({"announcements": results})
        except Exception as e:
            return jsonify({"msg": f"搜索失败: {str(e)}"}), 500

    # ============================================
    # 创建公告 API
    # ============================================
    @api_bp.route("/announcement", methods=["POST"])
    def api_create_announcement():
        """
        创建公告

        请求体:
        {
            "title": "公告标题",
            "content": "公告内容",
            "is_top": false
        }
        """
        try:
            auth_header = request.headers.get("Authorization")
            if not auth_header:
                return jsonify({"msg": "未登录"}), 401

            data = request.get_json()
            if not data:
                return jsonify({"msg": "请求体不能为空"}), 400

            title = data.get("title")
            content = data.get("content")
            is_top = data.get("is_top", False)

            if not title or not content:
                return jsonify({"msg": "标题和内容不能为空"}), 400

            # 假设从 token 获取用户信息
            announcement_id = AnnouncementService.create_announcement(
                title=title,
                content=content,
                author_id=1,
                author_name="test_user",
                is_top=1 if is_top else 0
            )

            return jsonify({
                "msg": "公告创建成功",
                "announcement_id": announcement_id
            }), 201

        except Exception as e:
            return jsonify({"msg": f"创建公告失败: {str(e)}"}), 500

    # ============================================
    # 删除公告 API - 未授权访问
    # ============================================
    @api_bp.route("/announcement/<int:announcement_id>", methods=["DELETE"])
    def api_delete_announcement(announcement_id):
        """
        删除公告 - 未授权访问漏洞演示

        漏洞: 没有任何权限检查，任何人可以删除任意公告
        攻击者只需要知道公告 ID 就能删除

        攻击示例:
        DELETE /api/announcement/1
        DELETE /api/announcement/2
        """
        try:
            AnnouncementService.delete_announcement(announcement_id)
            return jsonify({"msg": "删除成功"})
        except Exception as e:
            return jsonify({"msg": f"删除公告失败: {str(e)}"}), 500

    # ============================================
    # 获取公告访问统计 API - 敏感数据泄露
    # ============================================
    @api_bp.route("/announcement/<int:announcement_id>/stats", methods=["GET"])
    def api_get_announcement_stats(announcement_id):
        """
        获取公告访问统计 - 敏感数据泄露

        返回浏览量、评论数等信息
        这些数据可能对竞争对手有价值
        """
        try:
            announcement = AnnouncementService.get_announcement_by_id(announcement_id)
            if not announcement:
                return jsonify({"msg": "公告不存在"}), 404

            comments = AnnouncementService.get_comments_by_announcement(announcement_id)

            return jsonify({
                "announcement_id": announcement_id,
                "view_count": announcement.get("view_count", 0),
                "comment_count": len(comments),
                "is_top": announcement.get("is_top", 0) == 1
            })

        except Exception as e:
            return jsonify({"msg": f"获取统计失败: {str(e)}"}), 500

    # ============================================
    # 批量删除公告 API
    # ============================================
    @api_bp.route("/announcements/batch-delete", methods=["POST"])
    def api_batch_delete_announcements():
        """
        批量删除公告

        请求体:
        {
            "ids": [1, 2, 3]
        }
        """
        try:
            data = request.get_json()
            if not data:
                return jsonify({"msg": "请求体不能为空"}), 400

            ids = data.get("ids", [])
            if not ids:
                return jsonify({"msg": "缺少 IDs"}), 400

            deleted_count = 0
            for announcement_id in ids:
                try:
                    AnnouncementService.delete_announcement(announcement_id)
                    deleted_count += 1
                except:
                    pass

            return jsonify({
                "msg": "批量删除完成",
                "deleted_count": deleted_count
            })

        except Exception as e:
            return jsonify({"msg": f"批量删除失败: {str(e)}"}), 500