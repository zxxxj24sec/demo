"""
API 认证模块
包含登录、注册、Token 管理等功能
故意设计了多个 JWT 安全漏洞用于学习
"""
import jwt
import datetime
from flask import request, jsonify, current_app, session
from api import api_bp
from services.user_service import UserService

# ============================================
# JWT 安全漏洞配置 - 这些是故意留下的漏洞！
# ============================================

# 漏洞1: 弱密钥（用于演示暴力破解 JWT）
WEAK_SECRET_KEY = "secret123"
STRONG_SECRET_KEY = "ThisIsAVeryLongAndComplexSecretKeyThatShouldBeUsedInProduction123456789"

# 漏洞2: 支持 none 算法（经典 JWT 漏洞）
ALLOWED_ALGORITHMS = ["HS256", "HS512", "none"]


def generate_token_v1(username, is_admin=False):
    """
    生成 JWT Token - 使用弱密钥（漏洞版本）
    攻击者可以爆破这个弱密钥来伪造任意用户的 token
    """
    payload = {
        "username": username,
        "is_admin": is_admin,
        "exp": datetime.datetime.utcnow() + datetime.timedelta(days=7)
    }
    # 使用弱密钥，容易被爆破
    token = jwt.encode(payload, WEAK_SECRET_KEY, algorithm="HS256")
    return token


def generate_token_v2(username, is_admin=False):
    """
    生成 JWT Token - 正确版本（使用强密钥）
    """
    payload = {
        "username": username,
        "is_admin": is_admin,
        "exp": datetime.datetime.utcnow() + datetime.timedelta(days=7)
    }
    token = jwt.encode(payload, STRONG_SECRET_KEY, algorithm="HS256")
    return token


def verify_token_v1(token):
    """
    验证 Token - 支持 none 算法的漏洞版本
    攻击者可以将 algorithm 设置为 "none" 并移除签名
    """
    try:
        # 故意不限制算法，允许 "none"
        payload = jwt.decode(token, options={"verify_signature": False})
        return payload
    except jwt.exceptions.DecodeError:
        return None


def verify_token_v2(token):
    """
    验证 Token - 验证签名但使用弱密钥
    """
    try:
        # 使用弱密钥验证
        payload = jwt.decode(token, WEAK_SECRET_KEY, algorithms=["HS256"])
        return payload
    except jwt.exceptions.ExpiredSignatureError:
        return {"error": "Token 已过期"}
    except jwt.exceptions.DecodeError:
        return None


def register_auth_api(app):
    """
    注册 API 认证路由
    """
    app.register_blueprint(api_bp)

    # ============================================
    # 登录 API
    # ============================================
    @api_bp.route("/login", methods=["POST"])
    def api_login():
        """
        用户登录 API

        请求体:
        {
            "username": "admin",
            "password": "123456"
        }

        返回:
        {
            "msg": "login success",
            "token": "xxx",
            "user": {...}
        }
        """
        data = request.get_json()
        if not data:
            return jsonify({"msg": "请求体不能为空"}), 400

        username = data.get("username")
        password = data.get("password")

        if not username or not password:
            return jsonify({"msg": "用户名和密码不能为空"}), 400

        # 调用用户服务进行认证
        user = UserService.authenticate(username, password)

        if user:
            # 生成 token（使用弱密钥版本）
            token = generate_token_v1(username, user["is_admin"] == 1)

            # 漏洞: Token 在响应头中泄露
            response = jsonify({
                "msg": "登录成功",
                "token": token,
                "user": {
                    "id": user["id"],
                    "username": user["username"],
                    "is_admin": user["is_admin"] == 1
                }
            })
            # 故意在响应头中返回 token（不安全）
            response.headers["X-Auth-Token"] = token
            return response

        return jsonify({"msg": "用户名或密码错误"}), 401

    # ============================================
    # 注册 API
    # ============================================
    @api_bp.route("/register", methods=["POST"])
    def api_register():
        """
        用户注册 API

        请求体:
        {
            "username": "test",
            "password": "123456",
            "email": "test@example.com",
            "gender": "男"
        }
        """
        data = request.get_json()
        if not data:
            return jsonify({"msg": "请求体不能为空"}), 400

        username = data.get("username")
        password = data.get("password")
        email = data.get("email")
        gender = data.get("gender")

        if not username or not password:
            return jsonify({"msg": "用户名和密码不能为空"}), 400

        try:
            user_id = UserService.create_user(username, password, gender, email)
            return jsonify({
                "msg": "注册成功",
                "user_id": user_id
            }), 201
        except Exception as e:
            return jsonify({"msg": str(e)}), 400

    # ============================================
    # Token 验证 API
    # ============================================
    @api_bp.route("/verify", methods=["GET"])
    def api_verify():
        """
        验证 Token 是否有效

        请求头:
        Authorization: Bearer <token>

        返回:
        {
            "valid": true,
            "payload": {...}
        }
        """
        auth_header = request.headers.get("Authorization")
        if not auth_header:
            return jsonify({"valid": False, "msg": "缺少 Authorization 头"}), 401

        try:
            # 支持 Bearer token
            parts = auth_header.split()
            if len(parts) != 2 or parts[0] != "Bearer":
                return jsonify({"valid": False, "msg": "Authorization 格式错误"}), 401

            token = parts[1]

            # 使用漏洞版本验证（支持 none 算法）
            payload = verify_token_v1(token)

            if payload:
                return jsonify({
                    "valid": True,
                    "payload": payload
                })

            return jsonify({"valid": False, "msg": "无效的 Token"}), 401

        except Exception as e:
            return jsonify({"valid": False, "msg": f"Token 验证失败: {str(e)}"}), 401

    # ============================================
    # 获取当前用户信息 API
    # ============================================
    @api_bp.route("/me", methods=["GET"])
    def api_me():
        """
        获取当前登录用户信息

        请求头:
        Authorization: Bearer <token>
        """
        auth_header = request.headers.get("Authorization")
        if not auth_header:
            return jsonify({"msg": "未登录"}), 401

        try:
            parts = auth_header.split()
            if len(parts) != 2 or parts[0] != "Bearer":
                return jsonify({"msg": "Authorization 格式错误"}), 401

            token = parts[1]

            # 使用漏洞版本验证
            payload = verify_token_v1(token)

            if not payload or "username" not in payload:
                return jsonify({"msg": "无效的 Token"}), 401

            username = payload["username"]
            user = UserService.get_user_by_username(username)

            if not user:
                return jsonify({"msg": "用户不存在"}), 404

            return jsonify({
                "id": user["id"],
                "username": user["username"],
                "email": user.get("email"),
                "gender": user.get("gender"),
                "is_admin": user["is_admin"] == 1
            })

        except Exception as e:
            return jsonify({"msg": f"获取用户信息失败: {str(e)}"}), 500

    # ============================================
    # 修改密码 API（无旧密码验证 - 业务逻辑漏洞）
    # ============================================
    @api_bp.route("/change-password", methods=["POST"])
    def api_change_password():
        """
        修改密码 API

        请求体:
        {
            "new_password": "newpass123"
        }

        漏洞: 不验证旧密码，任何知道 token 的人都可以修改密码
        """
        auth_header = request.headers.get("Authorization")
        if not auth_header:
            return jsonify({"msg": "未登录"}), 401

        data = request.get_json()
        if not data:
            return jsonify({"msg": "请求体不能为空"}), 400

        new_password = data.get("new_password")
        if not new_password:
            return jsonify({"msg": "新密码不能为空"}), 400

        try:
            parts = auth_header.split()
            if len(parts) != 2 or parts[0] != "Bearer":
                return jsonify({"msg": "Authorization 格式错误"}), 401

            token = parts[1]
            payload = verify_token_v1(token)

            if not payload or "username" not in payload:
                return jsonify({"msg": "无效的 Token"}), 401

            username = payload["username"]
            user = UserService.get_user_by_username(username)

            if not user:
                return jsonify({"msg": "用户不存在"}), 404

            # 更新密码（不验证旧密码 - 漏洞）
            UserService.update_user(user["id"], password=new_password)

            return jsonify({"msg": "密码修改成功"})

        except Exception as e:
            return jsonify({"msg": f"修改密码失败: {str(e)}"}), 500

    # ============================================
    # 退出登录 API（只是简单返回成功，Token 仍然有效 - 设计缺陷）
    # ============================================
    @api_bp.route("/logout", methods=["POST"])
    def api_logout():
        """
        退出登录 API

        漏洞: 仅仅返回成功，Token 仍然有效
        攻击者可以继续使用这个 token
        正确做法应该是将 token 加入黑名单
        """
        return jsonify({"msg": "退出登录成功"})

    # ============================================
    # JWT 密钥探测接口（演示用）
    # ============================================
    @api_bp.route("/jwt/crack", methods=["POST"])
    def api_jwt_crack():
        """
        模拟 JWT 密钥爆破

        请求体:
        {
            "token": "eyJhbGciOi...",
            "wordlist": ["secret123", "password", "123456"]
        }

        这个接口用于学习 JWT 爆破攻击的原理
        """
        data = request.get_json()
        if not data:
            return jsonify({"msg": "请求体不能为空"}), 400

        token = data.get("token")
        wordlist = data.get("wordlist", [])

        if not token:
            return jsonify({"msg": "Token 不能为空"}), 400

        # 模拟暴力破解过程
        for word in wordlist:
            try:
                jwt.decode(token, word, algorithms=["HS256"])
                return jsonify({
                    "cracked": True,
                    "secret": word,
                    "message": f"密钥已找到: {word}"
                })
            except:
                continue

        return jsonify({
            "cracked": False,
            "message": "密钥未在词表中找到"
        })

    # ============================================
    # JWT none 算法演示
    # ============================================
    @api_bp.route("/jwt/none", methods=["GET"])
    def api_jwt_none():
        """
        演示 JWT none 算法漏洞

        攻击者可以将 token 的 algorithm 设置为 "none"
        然后移除签名部分，即可伪造任意用户身份

        返回一个使用 none 算法的示例 token
        """
        # 构造一个 algorithm 为 none 的 payload
        header = {"alg": "none", "typ": "JWT"}
        payload = {
            "username": "admin",
            "is_admin": True,
            "exp": datetime.datetime.utcnow() + datetime.timedelta(hours=1)
        }

        # none 算法不需要签名
        import base64
        import json

        def b64encode(data):
            return base64.urlsafe_b64encode(
                json.dumps(data).encode()
            ).decode().rstrip("=")

        header_b64 = b64encode(header)
        payload_b64 = b64encode(payload)

        # 注意：末尾没有签名部分，只有一个点
        malicious_token = f"{header_b64}.{payload_b64}."

        return jsonify({
            "original_algorithm": "none",
            "malicious_token": malicious_token,
            "warning": "这是演示 none 算法漏洞的恶意 token",
            "usage": "将 Authorization 头设置为: Bearer " + malicious_token
        })