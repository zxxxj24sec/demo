"""
API 用户管理模块
包含用户列表、详情、编辑等功能
故意设计了多个安全漏洞用于学习：
1. IDOR 越权漏洞
2. 水平权限绕过
3. 垂直权限提升
"""
import jwt
from flask import request, jsonify
from api import api_bp
from services.user_service import UserService
from api.auth import verify_token_v1

# 弱密钥（用于验证 token）
WEAK_SECRET_KEY = "secret123"


def get_current_user_from_token():
    """
    从请求头获取当前用户
    """
    auth_header = request.headers.get("Authorization")
    if not auth_header:
        return None

    try:
        parts = auth_header.split()
        if len(parts) != 2 or parts[0] != "Bearer":
            return None

        token = parts[1]
        payload = verify_token_v1(token)
        return payload
    except:
        return None


def register_user_api(app):
    """
    注册 API 用户管理路由
    """

    # ============================================
    # 获取所有用户列表 API
    # ============================================
    @api_bp.route("/users", methods=["GET"])
    def api_get_users():
        """
        获取所有用户列表

        返回:
        {
            "users": [
                {"id": 1, "username": "admin", "is_admin": true, ...},
                {"id": 2, "username": "test", "is_admin": false, ...}
            ]
        }

        漏洞: 任何人都可以访问，不需要登录
        """
        try:
            users = UserService.get_all_users()

            # 过滤敏感字段（但仍然泄露了用户存在性）
            safe_users = []
            for user in users:
                safe_users.append({
                    "id": user["id"],
                    "username": user["username"],
                    "is_admin": user["is_admin"] == 1,
                    "gender": user.get("gender"),
                    "email": user.get("email")
                })

            return jsonify({"users": safe_users})

        except Exception as e:
            return jsonify({"msg": f"获取用户列表失败: {str(e)}"}), 500

    # ============================================
    # 获取指定用户信息 API - IDOR 漏洞演示
    # ============================================
    @api_bp.route("/user/<int:user_id>", methods=["GET"])
    def api_get_user(user_id):
        """
        获取指定用户信息 - IDOR 漏洞演示

        正常请求:
        GET /api/user/1

        IDOR 攻击:
        GET /api/user/2  (普通用户)
        GET /api/user/3  (另一个普通用户)

        漏洞: 没有验证当前登录用户是否有权限访问目标用户的信息
        攻击者可以通过遍历 user_id 查看任意用户的信息
        """
        try:
            user = UserService.get_user_by_id(user_id)

            if not user:
                return jsonify({"msg": "用户不存在"}), 404

            # 直接返回用户所有信息，没有权限检查
            return jsonify({
                "id": user["id"],
                "username": user["username"],
                "password": user["password"],  # 漏洞: 密码也被返回了
                "is_admin": user["is_admin"] == 1,
                "gender": user.get("gender"),
                "email": user.get("email"),
                "avatar": user.get("avatar")
            })

        except Exception as e:
            return jsonify({"msg": f"获取用户信息失败: {str(e)}"}), 500

    # ============================================
    # 更新用户信息 API - 水平权限绕过漏洞
    # ============================================
    @api_bp.route("/user/<int:user_id>", methods=["PUT", "POST"])
    def api_update_user(user_id):
        """
        更新用户信息 - 水平权限绕过漏洞演示

        请求体:
        {
            "email": "newemail@example.com",
            "gender": "女"
        }

        漏洞: 没有验证当前登录用户是否有权限修改目标用户的信息
        普通用户 A 可以修改普通用户 B 的信息

        攻击示例:
        POST /api/user/2
        {
            "email": "attacker@evil.com"
        }
        """
        try:
            # 获取当前登录用户（但没有验证权限）
            current_user = get_current_user_from_token()

            # 这里应该有权限检查，但故意省略了（漏洞）
            # 应该检查: current_user["username"] == target_user["username"] or current_user["is_admin"]

            data = request.get_json()
            if not data:
                return jsonify({"msg": "请求体不能为空"}), 400

            # 直接更新用户信息，没有权限验证
            updated_user = UserService.update_user(
                user_id,
                username=data.get("username"),
                password=data.get("password"),
                gender=data.get("gender"),
                email=data.get("email")
            )

            return jsonify({
                "msg": "更新成功",
                "user": {
                    "id": updated_user["id"],
                    "username": updated_user["username"],
                    "email": updated_user.get("email"),
                    "gender": updated_user.get("gender")
                }
            })

        except Exception as e:
            return jsonify({"msg": f"更新用户信息失败: {str(e)}"}), 500

    # ============================================
    # 删除用户 API - 未授权访问漏洞
    # ============================================
    @api_bp.route("/user/<int:user_id>", methods=["DELETE"])
    def api_delete_user(user_id):
        """
        删除用户 - 未授权访问漏洞演示

        漏洞: 没有任何权限检查，任何知道 API 地址的人都可以删除用户

        攻击示例:
        DELETE /api/user/2
        DELETE /api/user/3
        DELETE /api/user/1  (甚至可以删除 admin)
        """
        try:
            # 没有任何检查
            UserService.delete_user(user_id)

            return jsonify({"msg": "删除成功"})

        except Exception as e:
            return jsonify({"msg": f"删除用户失败: {str(e)}"}), 500

    # ============================================
    # 获取用户成绩/课程信息 API - 敏感数据泄露
    # ============================================
    @api_bp.route("/user/<int:user_id>/grades", methods=["GET"])
    def api_get_user_grades(user_id):
        """
        获取用户成绩信息 - 敏感数据泄露漏洞演示

        漏洞: 任何登录用户都可以查看其他用户的成绩

        攻击示例:
        GET /api/user/1/grades
        GET /api/user/2/grades
        """
        # 模拟成绩数据（正常应该从数据库获取）
        grades_data = {
            1: {"math": 95, "english": 88, "science": 92},
            2: {"math": 78, "english": 82, "science": 75},
            3: {"math": 88, "english": 91, "science": 85}
        }

        if user_id not in grades_data:
            return jsonify({"msg": "成绩信息不存在"}), 404

        # 直接返回，没有验证权限
        return jsonify({
            "user_id": user_id,
            "grades": grades_data[user_id]
        })

    # ============================================
    # 修改用户角色 API - 垂直权限提升漏洞
    # ============================================
    @api_bp.route("/user/<int:user_id>/role", methods=["PUT", "POST"])
    def api_update_user_role(user_id):
        """
        修改用户角色 - 垂直权限提升漏洞演示

        请求体:
        {
            "is_admin": true
        }

        漏洞: 普通用户可以将自己或他人提升为管理员

        攻击示例:
        POST /api/user/2/role
        {
            "is_admin": true
        }

        危害: 普通用户可以获得完全的管理员权限
        """
        try:
            data = request.get_json()
            if not data:
                return jsonify({"msg": "请求体不能为空"}), 400

            is_admin = data.get("is_admin", False)

            # 没有验证当前用户是否是管理员，直接更新
            UserService.update_user(user_id, is_admin=1 if is_admin else 0)

            return jsonify({
                "msg": "角色更新成功",
                "is_admin": is_admin
            })

        except Exception as e:
            return jsonify({"msg": f"修改用户角色失败: {str(e)}"}), 500

    # ============================================
    # 批量操作用户 API - 条件竞争漏洞
    # ============================================
    @api_bp.route("/users/batch", methods=["POST"])
    def api_batch_update_users():
        """
        批量操作用户 - 条件竞争漏洞演示

        请求体:
        {
            "operations": [
                {"action": "delete", "user_id": 2},
                {"action": "update", "user_id": 3, "data": {"email": "test"}}
            ]
        }

        漏洞: 在高并发情况下，批量操作可能导致数据不一致
        """
        try:
            data = request.get_json()
            if not data:
                return jsonify({"msg": "请求体不能为空"}), 400

            operations = data.get("operations", [])
            results = []

            for op in operations:
                try:
                    action = op.get("action")
                    user_id = op.get("user_id")

                    if action == "delete":
                        UserService.delete_user(user_id)
                        results.append({"user_id": user_id, "status": "deleted"})
                    elif action == "update":
                        update_data = op.get("data", {})
                        UserService.update_user(user_id, **update_data)
                        results.append({"user_id": user_id, "status": "updated"})

                except Exception as e:
                    results.append({"user_id": op.get("user_id"), "status": "failed", "error": str(e)})

            return jsonify({
                "msg": "批量操作完成",
                "results": results
            })

        except Exception as e:
            return jsonify({"msg": f"批量操作失败: {str(e)}"}), 500