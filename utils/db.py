"""
数据库连接工具模块
负责封装数据库连接逻辑，提供统一的数据库操作接口
"""
import pymysql
import config


def get_db_connection():
    """
    获取数据库连接
    :return: 数据库连接对象
    """
    try:
        db = pymysql.connect(
            host=config.MYSQL_HOST,
            user=config.MYSQL_USER,
            password=config.MYSQL_PASSWORD,
            database=config.MYSQL_DATABASE,
            cursorclass=pymysql.cursors.DictCursor  # 返回字典格式的结果
        )
        return db
    except Exception as e:
        print(f"数据库连接失败: {str(e)}")
        raise


def execute_query(sql, params=None):
    """
    执行查询语句
    :param sql: SQL 查询语句
    :param params: 参数列表（用于参数化查询）
    :return: 查询结果列表
    """
    db = get_db_connection()
    try:
        with db.cursor() as cursor:
            cursor.execute(sql, params)
            result = cursor.fetchall()
            return result
    finally:
        db.close()


def execute_one(sql, params=None):
    """
    执行查询语句，返回单条结果
    :param sql: SQL 查询语句
    :param params: 参数列表（用于参数化查询）
    :return: 单条查询结果
    """
    db = get_db_connection()
    try:
        with db.cursor() as cursor:
            cursor.execute(sql, params)
            result = cursor.fetchone()
            return result
    finally:
        db.close()


def execute_update(sql, params=None):
    """
    执行更新语句（INSERT、UPDATE、DELETE）
    :param sql: SQL 更新语句
    :param params: 参数列表（用于参数化查询）
    :return: 受影响的行数
    """
    db = get_db_connection()
    try:
        with db.cursor() as cursor:
            cursor.execute(sql, params)
            db.commit()
            return cursor.rowcount
    except Exception as e:
        db.rollback()
        raise e
    finally:
        db.close()