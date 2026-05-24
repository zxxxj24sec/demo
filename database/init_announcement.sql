-- 公告系统数据库初始化脚本
-- 创建公告表
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

-- 创建公告评论表
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

-- 插入测试公告数据
INSERT INTO announcements (title, content, author_id, author_name, is_top) VALUES
('欢迎使用学校管理系统', '欢迎各位老师和学生使用本学校管理系统！如有疑问请联系管理员。', 1, 'admin', 1),
('本周重要通知', '本周五下午3点将在多功能厅举行全校大会，请全体师生准时参加。', 1, 'admin', 0);
