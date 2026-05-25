"""
修复评论表缺少 username 字段的问题
"""
import pymysql
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import config

def fix_comment_table():
    try:
        db = pymysql.connect(
            host=config.MYSQL_HOST,
            user=config.MYSQL_USER,
            password=config.MYSQL_PASSWORD,
            database=config.MYSQL_DATABASE
        )
        cursor = db.cursor()
        
        # 添加 username 字段
        cursor.execute('ALTER TABLE announcement_comments ADD COLUMN username VARCHAR(50) NOT NULL COMMENT "评论用户名" AFTER user_id')
        db.commit()
        print('添加 username 字段成功')
        
        # 如果已有评论数据，填充 username（从用户表获取）
        cursor.execute('SELECT * FROM announcement_comments')
        comments = cursor.fetchall()
        if comments:
            print(f'发现 {len(comments)} 条评论，尝试填充用户名...')
            for comment in comments:
                comment_id = comment[0]
                user_id = comment[2]
                cursor.execute('SELECT username FROM users WHERE id = %s', (user_id,))
                user = cursor.fetchone()
                if user:
                    username = user[0]
                    cursor.execute('UPDATE announcement_comments SET username = %s WHERE id = %s', (username, comment_id))
            db.commit()
            print('用户名填充完成')
        
        db.close()
        print('修复完成！')
        
    except Exception as e:
        print(f'修复失败: {str(e)}')
        raise

if __name__ == '__main__':
    fix_comment_table()