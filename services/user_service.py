"""
用户业务逻辑服务模块
封装用户相关的业务逻辑，包括用户认证、用户管理等功能
"""
from utils.db import execute_query, execute_one, execute_update


class UserService:
    """
    用户服务类
    提供用户相关的业务操作方法
    """

    @staticmethod
    def get_user_by_username(username):
        """
        根据用户名获取用户信息
        :param username: 用户名
        :return: 用户信息字典，如果不存在返回 None
        """
        sql = "SELECT * FROM users WHERE username = %s"
        result = execute_one(sql, (username,))
        return result

    @staticmethod
    def get_user_by_id(user_id):
        """
        根据用户ID获取用户信息
        :param user_id: 用户ID
        :return: 用户信息字典，如果不存在返回 None
        """
        sql = "SELECT * FROM users WHERE id = %s"
        result = execute_one(sql, (user_id,))
        return result

    @staticmethod
    def get_all_users():
        """
        获取所有用户列表
        :return: 用户列表
        """
        sql = "SELECT * FROM users"
        result = execute_query(sql)
        return result

    @staticmethod
    def create_user(username, password, gender=None, email=None):
        """
        创建新用户
        :param username: 用户名
        :param password: 密码
        :param gender: 性别（可选）
        :param email: 邮箱（可选）
        :return: 新创建用户的ID
        :raises: Exception 如果用户名已存在
        """
        # 检查用户名是否已存在
        existing_user = UserService.get_user_by_username(username)
        if existing_user:
            raise Exception("用户名已存在")

        # 插入新用户
        sql = """
            INSERT INTO users (username, password, is_admin, gender, email)
            VALUES (%s, %s, 0, %s, %s)
        """
        rowcount = execute_update(sql, (username, password, gender, email))
        
        # 获取新插入用户的ID
        if rowcount > 0:
            new_user = UserService.get_user_by_username(username)
            return new_user['id'] if new_user else None
        return None

    @staticmethod
    def update_user(user_id, username=None, password=None, gender=None, email=None, avatar=None):
        """
        更新用户信息
        :param user_id: 用户ID
        :param username: 新用户名（可选）
        :param password: 新密码（可选）
        :param gender: 新性别（可选）
        :param email: 新邮箱（可选）
        :param avatar: 头像文件名（可选）
        :return: 更新后的用户信息
        :raises: Exception 如果用户不存在
        """
        # 检查用户是否存在
        existing_user = UserService.get_user_by_id(user_id)
        if not existing_user:
            raise Exception("用户不存在")

        # 构建更新字段
        update_fields = []
        params = []

        if username:
            update_fields.append("username = %s")
            params.append(username)
        if password:
            update_fields.append("password = %s")
            params.append(password)
        if gender is not None:
            update_fields.append("gender = %s")
            params.append(gender)
        if email is not None:
            update_fields.append("email = %s")
            params.append(email)
        if avatar is not None:
            update_fields.append("avatar = %s")
            params.append(avatar)

        if not update_fields:
            raise Exception("没有需要更新的字段")

        params.append(user_id)
        sql = f"UPDATE users SET {', '.join(update_fields)} WHERE id = %s"
        execute_update(sql, params)

        return UserService.get_user_by_id(user_id)

    @staticmethod
    def delete_user(user_id):
        """
        删除用户
        :param user_id: 用户ID
        :return: 删除是否成功
        :raises: Exception 如果用户不存在
        """
        # 检查用户是否存在
        existing_user = UserService.get_user_by_id(user_id)
        if not existing_user:
            raise Exception("用户不存在")

        sql = "DELETE FROM users WHERE id = %s"
        rowcount = execute_update(sql, (user_id,))
        return rowcount > 0

    @staticmethod
    def authenticate(username, password):
        """
        用户认证（登录验证）
        :param username: 用户名
        :param password: 密码
        :return: 用户信息字典，如果认证失败返回 None
        """
        sql = "SELECT * FROM users WHERE username = %s AND password = %s"
        result = execute_one(sql, (username, password))
        return result

    @staticmethod
    def is_admin(username):
        """
        检查用户是否为管理员
        :param username: 用户名
        :return: True 如果是管理员，False 否则
        """
        user = UserService.get_user_by_username(username)
        if user and user.get('is_admin') == 1:
            return True
        return False