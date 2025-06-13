import os
import psutil
from service.database_service import DatabaseService
from flask import jsonify
from collections import defaultdict
from collections import OrderedDict


def get_platform_stats():
    """
    获取平台统计信息
    返回：评价总数、学校学院统计、用户总数、内存占用
    """
    # 移除多余的 try 语句块
    # 1. 获取评价总数
    review_db = DatabaseService('professor')
    review_count = review_db.execute_query(
        "SELECT COUNT(*) FROM review_sentences",
        fetch_one=True
    )[0]

    # 2. 获取学校/学院统计
    school_stats = review_db.execute_query('''
        SELECT university, department, COUNT(*) as count 
        FROM professor 
        GROUP BY university, department
    ''')

    # 处理成层级结构
    school_data = defaultdict(lambda: {"departments": {}, "total": 0})
    for uni, dept, count in school_stats:
        school_data[uni]["departments"][dept] = count
        school_data[uni]["total"] += count

    # 3. 获取用户总数
    user_db = DatabaseService('user')
    user_count = user_db.execute_query(
        "SELECT COUNT(*) FROM user",
        fetch_one=True
    )[0]

    # 4. 获取内存占用（单位：MB）
    process = psutil.Process(os.getpid())
    memory_usage = round(process.memory_info().rss / 1024 / 1024, 2)

    return jsonify({
        "review_count": review_count,
        "schools": school_data,
        "user_count": user_count,
        "memory_usage": f"{memory_usage} MB"
    })


from collections import OrderedDict


def get_all_users_information():
    """
    获取所有用户及其评价信息
    返回结构：
    {
        "users": [
            {
                "user_id": "用户ID",
                "role": "角色",
                "review_allowed": "是否允许评价",
                "reviews": [ ... ]
            },
            ...更多用户
        ]
    }
    """
    try:
        user_db = DatabaseService('user')
        professor_db = DatabaseService('professor')

        # 获取所有用户基本信息
        users = user_db.execute_query('''
            SELECT u.user_id, u.role, u.review_allowed 
            FROM user u
        ''')

        # 使用OrderedDict确保字段顺序
        result = {"users": []}
        for user in users:
            user_id = user[0]
            role = user[1]
            review_allowed = user[2]

            # 获取用户的所有评价
            reviews = professor_db.execute_query('''
                SELECT s.sentence_id, p.name, p.university, p.department, 
                       s.review_sentence
                FROM review_sentences s
                JOIN professor p ON s.tutor_id = p.tutor_id
                WHERE s.user_id = ?
            ''', (user_id,))

            # 使用OrderedDict确保字段顺序
            user_obj = OrderedDict()
            user_obj["user_id"] = user_id
            user_obj["role"] = role
            user_obj["review_allowed"] = review_allowed

            # 创建review列表
            review_list = []
            for row in reviews:
                review_dict = OrderedDict([
                    ("sentence_id", row[0]),
                    ("tutor_name", row[1]),
                    ("university", row[2]),
                    ("department", row[3]),
                    ("review_sentence", row[4])
                ])
                review_list.append(review_dict)

            user_obj["reviews"] = review_list

            result["users"].append(user_obj)

        return jsonify(result)

    except Exception as e:
        return jsonify({"error": str(e)}), 500