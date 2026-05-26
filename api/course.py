"""
API 课程管理模块
包含课程列表、成绩管理等功能
设计了一些安全漏洞用于学习：
1. 越权访问
2. 敏感数据泄露
3. 参数篡改
"""
from flask import request, jsonify
from api import api_bp
from services.user_service import UserService

# 模拟课程数据
COURSES = [
    {"id": 1, "name": "Python 编程基础", "teacher": "张老师", "credit": 3, "students": [1, 2, 3]},
    {"id": 2, "name": "Web 安全入门", "teacher": "李老师", "credit": 4, "students": [1, 2]},
    {"id": 3, "name": "数据库原理", "teacher": "王老师", "credit": 3, "students": [1, 3]},
    {"id": 4, "name": "网络攻防实战", "teacher": "刘老师", "credit": 5, "students": [1]},
]

# 模拟成绩数据
GRADES = {
    1: {  # user_id = 1 (admin)
        1: {"score": 95, "rank": 1},  # course_id: score info
        2: {"score": 88, "rank": 2},
        3: {"score": 92, "rank": 1},
        4: {"score": 90, "rank": 1}
    },
    2: {  # user_id = 2
        1: {"score": 78, "rank": 5},
        2: {"score": 82, "rank": 4}
    },
    3: {  # user_id = 3
        1: {"score": 85, "rank": 3},
        3: {"score": 88, "rank": 2}
    }
}


def register_course_api(app):
    """
    注册 API 课程管理路由
    """

    # ============================================
    # 获取课程列表 API
    # ============================================
    @api_bp.route("/courses", methods=["GET"])
    def api_get_courses():
        """
        获取课程列表

        返回:
        {
            "courses": [...]
        }

        漏洞: 任何人无需登录即可访问课程列表
        """
        try:
            return jsonify({"courses": COURSES})
        except Exception as e:
            return jsonify({"msg": f"获取课程列表失败: {str(e)}"}), 500

    # ============================================
    # 获取指定课程详情 API
    # ============================================
    @api_bp.route("/course/<int:course_id>", methods=["GET"])
    def api_get_course(course_id):
        """
        获取指定课程详情

        漏洞: 可以通过遍历 course_id 查看任意课程信息
        """
        for course in COURSES:
            if course["id"] == course_id:
                return jsonify({"course": course})

        return jsonify({"msg": "课程不存在"}), 404

    # ============================================
    # 获取课程成绩 API - 参数篡改漏洞
    # ============================================
    @api_bp.route("/course/<int:course_id>/grade", methods=["GET"])
    def api_get_course_grade(course_id):
        """
        获取课程成绩 - 参数篡改漏洞演示

        请求参数:
        ?user_id=1

        漏洞: 用户可以通过修改 user_id 参数查看他人的成绩

        攻击示例:
        GET /api/course/1/grade?user_id=1  (查看自己的成绩)
        GET /api/course/1/grade?user_id=2  (查看用户2的成绩)
        GET /api/course/2/grade?user_id=2  (查看用户2在课程2的成绩)
        """
        user_id = request.args.get("user_id", type=int)

        if not user_id:
            return jsonify({"msg": "缺少 user_id 参数"}), 400

        # 检查课程是否存在
        course_exists = any(c["id"] == course_id for c in COURSES)
        if not course_exists:
            return jsonify({"msg": "课程不存在"}), 404

        # 直接返回成绩，没有验证当前用户是否有权限
        user_grades = GRADES.get(user_id, {})
        course_grade = user_grades.get(course_id)

        if not course_grade:
            return jsonify({"msg": "成绩信息不存在"}), 404

        return jsonify({
            "user_id": user_id,
            "course_id": course_id,
            "score": course_grade["score"],
            "rank": course_grade["rank"]
        })

    # ============================================
    # 成绩修改 API - 业务逻辑漏洞
    # ============================================
    @api_bp.route("/course/<int:course_id>/grade", methods=["PUT", "POST"])
    def api_update_course_grade(course_id):
        """
        修改成绩 - 业务逻辑漏洞演示

        请求体:
        {
            "user_id": 2,
            "score": 100
        }

        漏洞: 没有验证操作者权限，任何人可以修改任意成绩
        可以将成绩改得很高或很低
        """
        try:
            data = request.get_json()
            if not data:
                return jsonify({"msg": "请求体不能为空"}), 400

            user_id = data.get("user_id")
            score = data.get("score")

            if not user_id or score is None:
                return jsonify({"msg": "缺少必要参数"}), 400

            # 验证课程是否存在
            course_exists = any(c["id"] == course_id for c in COURSES)
            if not course_exists:
                return jsonify({"msg": "课程不存在"}), 404

            # 没有权限检查，直接修改成绩
            if user_id not in GRADES:
                GRADES[user_id] = {}

            GRADES[user_id][course_id] = {
                "score": score,
                "rank": 1  # 简单假设修改后排名第一
            }

            return jsonify({
                "msg": "成绩修改成功",
                "user_id": user_id,
                "course_id": course_id,
                "new_score": score
            })

        except Exception as e:
            return jsonify({"msg": f"修改成绩失败: {str(e)}"}), 500

    # ============================================
    # 获取所有成绩 API - 敏感数据批量泄露
    # ============================================
    @api_bp.route("/grades/all", methods=["GET"])
    def api_get_all_grades():
        """
        获取所有成绩 - 敏感数据批量泄露漏洞

        漏洞: 管理员（或者攻击者）可以一次性获取所有学生的所有成绩
        这是过度数据暴露的例子
        """
        return jsonify({
            "grades": GRADES,
            "warning": "这是敏感数据，请妥善保管！"
        })

    # ============================================
    # 选课 API - 竞争条件漏洞
    # ============================================
    @api_bp.route("/course/<int:course_id>/enroll", methods=["POST"])
    def api_enroll_course(course_id):
        """
        选课 - 竞争条件漏洞演示

        请求体:
        {
            "user_id": 1
        }

        漏洞: 在高并发情况下，可能出现超额选课的情况
        例如：课程容量为30人，但最终选了35人
        """
        try:
            data = request.get_json()
            if not data:
                return jsonify({"msg": "请求体不能为空"}), 400

            user_id = data.get("user_id")
            if not user_id:
                return jsonify({"msg": "缺少 user_id"}), 400

            # 检查课程是否存在
            course = None
            for c in COURSES:
                if c["id"] == course_id:
                    course = c
                    break

            if not course:
                return jsonify({"msg": "课程不存在"}), 404

            # 检查是否已经选过
            if user_id in course["students"]:
                return jsonify({"msg": "已经选过这门课"}), 400

            # 没有检查课程容量限制（漏洞）
            course["students"].append(user_id)

            return jsonify({
                "msg": "选课成功",
                "course_id": course_id,
                "user_id": user_id
            })

        except Exception as e:
            return jsonify({"msg": f"选课失败: {str(e)}"}), 500

    # ============================================
    # 退课 API
    # ============================================
    @api_bp.route("/course/<int:course_id>/drop", methods=["POST"])
    def api_drop_course(course_id):
        """
        退课

        请求体:
        {
            "user_id": 1
        }
        """
        try:
            data = request.get_json()
            if not data:
                return jsonify({"msg": "请求体不能为空"}), 400

            user_id = data.get("user_id")
            if not user_id:
                return jsonify({"msg": "缺少 user_id"}), 400

            # 检查课程是否存在
            course = None
            for c in COURSES:
                if c["id"] == course_id:
                    course = c
                    break

            if not course:
                return jsonify({"msg": "课程不存在"}), 404

            # 检查是否选过这门课
            if user_id not in course["students"]:
                return jsonify({"msg": "没有选过这门课"}), 400

            course["students"].remove(user_id)

            return jsonify({
                "msg": "退课成功",
                "course_id": course_id,
                "user_id": user_id
            })

        except Exception as e:
            return jsonify({"msg": f"退课失败: {str(e)}"}), 500

    # ============================================
    # 获取课程学生列表 API
    # ============================================
    @api_bp.route("/course/<int:course_id>/students", methods=["GET"])
    def api_get_course_students(course_id):
        """
        获取课程学生列表

        漏洞: 任何人可以查看某门课的所有学生
        """
        for course in COURSES:
            if course["id"] == course_id:
                # 获取每个学生的详细信息（过度暴露）
                students_info = []
                for student_id in course["students"]:
                    user = UserService.get_user_by_id(student_id)
                    if user:
                        students_info.append({
                            "id": user["id"],
                            "username": user["username"],
                            "email": user.get("email"),
                            "gender": user.get("gender")
                        })

                return jsonify({
                    "course_id": course_id,
                    "course_name": course["name"],
                    "students": students_info
                })

        return jsonify({"msg": "课程不存在"}), 404