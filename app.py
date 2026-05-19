from flask import Flask, request, session, render_template   # 导入 Flask、请求对象、Session、模板渲染
import pymysql, config                      # 导入数据库驱动和配置

app = Flask(__name__)                       # 创建 Flask 应用

app.secret_key = "test1234"                 # Session 加密密钥


def is_admin(username):
    """
    检查用户是否为管理员
    :param username: 用户名
    :return: True 如果是管理员，False 否则
    """
    db = pymysql.connect(
        host=config.MYSQL_HOST,
        user=config.MYSQL_USER,
        password=config.MYSQL_PASSWORD,
        database=config.MYSQL_DATABASE
    )
    cursor = db.cursor()
    # 查询用户的管理员状态，is_admin 字段为 1 表示管理员，0 表示普通用户
    cursor.execute(f"SELECT is_admin FROM users WHERE username='{username}'")
    result = cursor.fetchone()
    db.close()
    
    # 如果查询到结果且 is_admin 字段为 1，则返回 True
    return result is not None and result[0] == 1


def get_user_by_id(user_id):
    """
    根据用户ID获取用户信息
    :param user_id: 用户ID
    :return: 用户信息元组，包含(id, username, password, is_admin)
    """
    db = pymysql.connect(
        host=config.MYSQL_HOST,
        user=config.MYSQL_USER,
        password=config.MYSQL_PASSWORD,
        database=config.MYSQL_DATABASE
    )
    cursor = db.cursor()
    cursor.execute(f"SELECT * FROM users WHERE id={user_id}")
    user = cursor.fetchone()
    db.close()
    return user


@app.route("/")                            # 首页路由
def index():
    return render_template("index.html")


@app.route("/login", methods=["GET", "POST"])  # 登录路由
def login():
    if request.method == "POST":
        username = request.form.get("username")
        password = request.form.get("password")

        db = pymysql.connect(
            host=config.MYSQL_HOST,
            user=config.MYSQL_USER,
            password=config.MYSQL_PASSWORD,
            database=config.MYSQL_DATABASE
        )
        cursor = db.cursor()

        sql = f"SELECT * FROM users WHERE username='{username}' AND password='{password}'"
        print("执行的 SQL:", sql)

        cursor.execute(sql)
        result = cursor.fetchone()
        db.close()

        if result:
            session["user"] = username
            # 将管理员状态存入 session，便于后续权限判断
            session["is_admin"] = result[3] == 1
            return render_template("login.html", success=True, username=username, sql=sql)

        return render_template("login.html", success=False, message="用户名或密码错误", sql=sql)
    
    return render_template("index.html")


@app.route("/profile")                     # 个人主页路由
def profile():
    if "user" in session:
        return render_template("profile.html", logged_in=True, username=session["user"], is_admin=session.get("is_admin", False))
    return render_template("profile.html", logged_in=False)


@app.route("/register", methods=["GET", "POST"])  # 注册路由
def register():
    if request.method == "POST":
        username = request.form.get("username")
        password = request.form.get("password")
        
        db = pymysql.connect(
            host=config.MYSQL_HOST,
            user=config.MYSQL_USER,
            password=config.MYSQL_PASSWORD,
            database=config.MYSQL_DATABASE
        )
        cursor = db.cursor()
        
        check_sql = f"SELECT * FROM users WHERE username='{username}'"
        cursor.execute(check_sql)
        if cursor.fetchone():
            db.close()
            return render_template("register.html", page="fail", message="用户名已存在")
        
        # 新注册用户默认不是管理员（is_admin=0）
        insert_sql = f"INSERT INTO users (username, password, is_admin) VALUES ('{username}', '{password}', 0)"
        try:
            cursor.execute(insert_sql)
            db.commit()
            db.close()
            return render_template("register.html", page="success")
        except Exception as e:
            db.rollback()
            db.close()
            return render_template("register.html", page="fail", message=f"错误：{str(e)}")
    
    return render_template("register.html", page="form")


@app.route("/logout")                      # 退出登录路由
def logout():
    session.pop("user", None)
    session.pop("is_admin", None)          # 清除管理员状态
    return render_template("logout.html")


@app.route("/users")                        # 用户列表路由
def users():
    # 检查用户是否已登录
    if "user" not in session:
        return render_template("login.html", success=False, message="请先登录")
    
    # 获取当前登录用户信息
    current_user = session["user"]
    current_is_admin = session.get("is_admin", False)
    
    # 连接数据库获取用户列表
    db = pymysql.connect(
        host=config.MYSQL_HOST,
        user=config.MYSQL_USER,
        password=config.MYSQL_PASSWORD,
        database=config.MYSQL_DATABASE
    )
    cursor = db.cursor()
    cursor.execute("SELECT * FROM users")   # 执行SQL查询，获取所有用户信息
    users_list = cursor.fetchall()          # 获取所有查询结果
    db.close()
    
    # 根据用户权限渲染不同的模板内容
    return render_template("users.html", 
                          users=users_list, 
                          current_user=current_user,
                          is_admin=current_is_admin)


@app.route("/user/<int:user_id>", methods=["GET", "POST"])  # 用户详情/编辑路由
def user_detail(user_id):
    # 检查用户是否已登录
    if "user" not in session:
        return render_template("login.html", success=False, message="请先登录")
    
    # 获取当前登录用户信息
    current_user = session["user"]
    current_is_admin = session.get("is_admin", False)
    
    # 根据用户ID获取目标用户信息
    user = get_user_by_id(user_id)
    
    # 如果用户不存在，返回错误信息
    if not user:
        return render_template("user_detail.html", user=None, success=False, message="用户不存在")
    
    # 获取目标用户的用户名
    target_username = user[1]
    
    # 权限检查：只有管理员或用户本人才能查看详情
    if not current_is_admin and current_user != target_username:
        return render_template("user_detail.html", user=None, success=False, 
                              message="权限不足：只能查看自己的用户详情")
    
    # 处理 POST 请求（编辑用户）
    if request.method == "POST":
        # 权限检查：只有管理员才能编辑用户
        if not current_is_admin:
            return render_template("user_detail.html", user={"id": user_id, "username": target_username}, 
                                  success=False, message="权限不足：只有管理员才能编辑用户")
        
        # 获取表单提交的新用户名和密码
        new_username = request.form.get("username")
        new_password = request.form.get("password")
        
        # 构建更新 SQL 语句
        if new_password:
            update_sql = f"UPDATE users SET username='{new_username}', password='{new_password}' WHERE id={user_id}"
        else:
            # 如果密码为空，则只更新用户名
            update_sql = f"UPDATE users SET username='{new_username}' WHERE id={user_id}"
        
        # 执行更新操作
        db = pymysql.connect(
            host=config.MYSQL_HOST,
            user=config.MYSQL_USER,
            password=config.MYSQL_PASSWORD,
            database=config.MYSQL_DATABASE
        )
        cursor = db.cursor()
        try:
            cursor.execute(update_sql)
            db.commit()
            db.close()
            return render_template("user_detail.html", 
                                  user={"id": user_id, "username": new_username}, 
                                  success=True, message="更新成功")
        except Exception as e:
            db.rollback()
            db.close()
            return render_template("user_detail.html", 
                                  user={"id": user_id, "username": target_username}, 
                                  success=False, message=f"更新失败：{str(e)}")
    else:
        # GET 请求：显示用户详情
        return render_template("user_detail.html", 
                              user={"id": user[0], "username": user[1], "password": user[2]}, 
                              success=True,
                              is_admin=current_is_admin)


@app.route("/user/delete/<int:user_id>")   # 删除用户路由
def delete_user(user_id):
    # 检查用户是否已登录
    if "user" not in session:
        return render_template("login.html", success=False, message="请先登录")
    
    # 权限检查：只有管理员才能删除用户
    if not session.get("is_admin", False):
        return render_template("users.html", users=None, success=False, 
                              message="权限不足：只有管理员才能删除用户", 
                              current_user=session["user"],
                              is_admin=False)
    
    # 获取要删除的用户信息
    user = get_user_by_id(user_id)
    if not user:
        return render_template("users.html", users=None, success=False, 
                              message="用户不存在", 
                              current_user=session["user"],
                              is_admin=True)
    
    # 执行删除操作
    db = pymysql.connect(
        host=config.MYSQL_HOST,
        user=config.MYSQL_USER,
        password=config.MYSQL_PASSWORD,
        database=config.MYSQL_DATABASE
    )
    cursor = db.cursor()
    
    try:
        cursor.execute(f"DELETE FROM users WHERE id={user_id}")
        db.commit()
        db.close()
        # 删除成功后重新获取用户列表
        db = pymysql.connect(
            host=config.MYSQL_HOST,
            user=config.MYSQL_USER,
            password=config.MYSQL_PASSWORD,
            database=config.MYSQL_DATABASE
        )
        cursor = db.cursor()
        cursor.execute("SELECT * FROM users")
        users_list = cursor.fetchall()
        db.close()
        return render_template("users.html", users=users_list, success=True, 
                              message="删除成功", 
                              current_user=session["user"],
                              is_admin=True)
    except Exception as e:
        db.rollback()
        db.close()
        return render_template("users.html", users=None, success=False, 
                              message=f"删除失败：{str(e)}", 
                              current_user=session["user"],
                              is_admin=True)


app.run(debug=True, host='0.0.0.0')