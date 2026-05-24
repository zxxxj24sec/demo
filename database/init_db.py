"""
数据库初始化脚本
创建公告系统所需的表
"""
import pymysql
import sys
import os

# 添加父目录到路径
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import config


def init_database():
    """初始化数据库表"""
    try:
        # 连接数据库
        db = pymysql.connect(
            host=config.MYSQL_HOST,
            user=config.MYSQL_USER,
            password=config.MYSQL_PASSWORD,
            database=config.MYSQL_DATABASE,
            cursorclass=pymysql.cursors.DictCursor
        )

        with db.cursor() as cursor:
            # 创建公告表
            create_announcements_table = """
                CREATE TABLE IF NOT EXISTS announcements (
                    id INT AUTO_INCREMENT PRIMARY KEY COMMENT '公告ID',
                    title VARCHAR(200) NOT NULL COMMENT '公告标题',
                    content TEXT NOT NULL COMMENT '公告内容',
                    author_id INT NOT NULL COMMENT '发布者用户ID',
                    author_name VARCHAR(50) NOT NULL COMMENT '发布者用户名',
                    is_top TINYINT(1) DEFAULT 0 COMMENT '是否置顶：0-否，1-是',
                    view_count INT DEFAULT 0 COMMENT '浏览次数',
                    created_at DATETIME DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
                    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
                    INDEX idx_author (author_id),
                    INDEX idx_created (created_at),
                    INDEX idx_top (is_top)
                ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='公告表';
            """
            cursor.execute(create_announcements_table)
            print("创建 announcements 表成功")

            # 创建公告评论表
            create_comments_table = """
                CREATE TABLE IF NOT EXISTS announcement_comments (
                    id INT AUTO_INCREMENT PRIMARY KEY COMMENT '评论ID',
                    announcement_id INT NOT NULL COMMENT '关联公告ID',
                    user_id INT NOT NULL COMMENT '评论用户ID',
                    username VARCHAR(50) NOT NULL COMMENT '评论用户名',
                    content TEXT NOT NULL COMMENT '评论内容',
                    created_at DATETIME DEFAULT CURRENT_TIMESTAMP COMMENT '评论时间',
                    INDEX idx_announcement (announcement_id),
                    INDEX idx_user (user_id)
                ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='公告评论表';
            """
            cursor.execute(create_comments_table)
            print("创建 announcement_comments 表成功")

            # 检查是否已有测试数据
            cursor.execute("SELECT COUNT(*) as count FROM announcements")
            result = cursor.fetchone()
            if result['count'] == 0:
                # 插入测试公告数据
                insert_test_data = """
                    INSERT INTO announcements (title, content, author_id, author_name, is_top) VALUES
                    ('欢迎使用学校管理系统', '欢迎各位老师和学生使用本学校管理系统！如有疑问请联系管理员。', 1, 'admin', 1),
                    ('本周重要通知', '本周五下午3点将在多功能厅举行全校大会，请全体师生准时参加。', 1, 'admin', 0);
                """
                cursor.execute(insert_test_data)
                print("插入测试数据成功")

        db.commit()
        print("数据库初始化完成！")

    except Exception as e:
        print(f"数据库初始化失败: {str(e)}")
        raise
    finally:
        if 'db' in locals():
            db.close()


if __name__ == "__main__":
    init_database()
