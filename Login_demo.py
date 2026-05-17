from flask import Flask, request, session   # 导入 Flask、请求对象、Session

app = Flask(__name__)                       # 创建 Flask 应用

app.secret_key = "test123"                 # Session 加密密钥

USER = "admin"                             # 模拟用户名
PASSWORD = "123456"                        # 模拟密码


@app.route("/")                            # 首页路由
def index():

    return '''
    <h1>Flask Login Demo</h1>              <!-- 页面标题 -->

    <form action="/login" method="get">   <!-- 登录表单 -->

        <input type="text"                 
               name="username"             
               placeholder="请输入用户名">   <!-- 用户名输入框 -->

        <br><br>

        <input type="password"             
               name="password"             
               placeholder="请输入密码">     <!-- 密码输入框 -->

        <br><br>

        <button type="submit">登录</button> <!-- 登录按钮 -->

    </form>

    <br>

    <a href="/profile">                    <!-- 跳转个人主页 -->
        <button>个人主页</button>
    </a>

    <br><br>

    <a href="/logout">                     <!-- 跳转退出登录 -->
        <button>退出登录</button>
    </a>
    '''


@app.route("/login")                       # 登录路由
def login():

    username = request.args.get("username") # 获取 username 参数
    password = request.args.get("password") # 获取 password 参数

    if username == USER and password == PASSWORD: # 验证账号密码

        session["user"] = username         # 写入 Session 保存登录状态

        return f'''
        <h1>login success</h1>             <!-- 登录成功提示 -->

        <h2>欢迎 {username}</h2>           <!-- 显示用户名 -->

        <a href="/profile">                <!-- 跳转个人主页 -->
            <button>进入个人主页</button>
        </a>

        <br><br>

        <a href="/logout">                 <!-- 跳转退出登录 -->
            <button>退出登录</button>
        </a>
        '''

    return '''
    <h1>login failed</h1>                  <!-- 登录失败提示 -->

    <a href="/">                           <!-- 返回首页 -->
        <button>重新登录</button>
    </a>
    '''


@app.route("/profile")                     # 个人主页路由
def profile():

    if "user" in session:                  # 判断是否已登录

        return f'''
        <h1>hello {session["user"]}</h1>   <!-- 显示 Session 中用户名 -->

        <a href="/logout">                 <!-- 跳转退出登录 -->
            <button>退出登录</button>
        </a>
        '''

    return '''
    <h1>please login first</h1>            <!-- 未登录提示 -->

    <a href="/">                           <!-- 返回首页 -->
        <button>返回首页</button>
    </a>
    '''


@app.route("/logout")                      # 退出登录路由
def logout():

    session.pop("user", None)              # 删除 Session 中 user 数据

    return '''
    <h1>logout success</h1>                <!-- 退出成功提示 -->

    <a href="/">                           <!-- 返回首页 -->
        <button>返回首页</button>
    </a>
    '''


app.run(debug=True, host='0.0.0.0')                        # 启动 Flask 调试模式