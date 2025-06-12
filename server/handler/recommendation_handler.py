"""
核心推荐引擎模块接口，提供导师推荐结果展示，导师详细信息查看功能
"""


from flask import Blueprint, request, jsonify
from service.recommendation_service import RecommendationService
from flask import session

# 创建推荐引擎蓝图
recommend_blue = Blueprint('recommendation', __name__, url_prefix='/recommend')


@recommend_blue.route('/get_recommendations', methods=['POST'])
def get_recommendations():
    """
    获取推荐结果接口
    功能：接收用户输入的查询文本，解析需求并返回推荐结果
    """
    data = request.json
    query = data.get('query', '').strip()  # 查询语句
    university = data.get('university', '').strip()  # 学校
    department = data.get('department', '').strip()  # 学院/系

    # 检查输入是否为空
    if not query:
        return jsonify({"error": "请输入查询内容"}), 400
    if not university:
        return jsonify({"error": "请输入学校"}), 400
    if not department:
        return jsonify({"error": "请输入学院/系"}), 400

    # 调用推荐服务获取结果（包含解析和推荐两个步骤）
    query_result = RecommendationService.get_recommendations(query, university, department)
    # 失败返回错误信息
    if not query_result["success"]:
        return jsonify({"error": query_result["message"]}), 400

    # 成功返回推荐结果
    return jsonify({"commend_result": query_result["message"]}), 200


@recommend_blue.route('/submit_review', methods=['POST'])
def submit_review():
    data = request.json
    user_id = session.get('user_id')

    # 权限校验
    from service.database_service import DatabaseService
    user_db = DatabaseService('user')
    user_info = user_db.get_user(user_id)

    # 检查权限字段（修复后这里会获取正确的review_allowed值）
    if user_info.get('review_allowed', 'True') != 'True':
        return jsonify({"error": "你已暂时被限制提交评价"}), 403

    # 原有参数校验保持不变
    required_fields = ['name', 'university', 'department', 'academic', 'responsibility', 'character']
    if not all(field in data for field in required_fields):
        return jsonify({"error": "缺少必要参数"}), 400

    result = RecommendationService.submit_review(data, user_id)

    if result["success"]:
        return jsonify({"message": result["message"]}), 200
    return jsonify({"error": result["message"]}), 400


@recommend_blue.route('/show_information', methods=['POST'])
def show_information():
    """
       导师信息展示接口
       功能：根据导师ID返回基本信息连接及评价内容
    """
    data = request.json
    tutor_id = data.get('tutor_id')

    if not tutor_id:
        return jsonify({"error": "缺少导师ID参数"}), 400

    result = RecommendationService.show_information(tutor_id)

    if result["success"]:
        return jsonify(result["data"]), 200
    return jsonify({"error": result["message"]}), 400


@recommend_blue.route('/get_all_reviews', methods=['GET'])
def get_all_reviews():
    """
    获取所有评价接口
    功能：返回所有评价的列表，包括评价ID、导师姓名、学校、学院/系、评价内容等
    :return: 包含所有评价的列表
    """
    result = RecommendationService.get_all_reviews()
    if not result["success"]:
        return jsonify({"error": result["message"]}), 400
    return jsonify(result)


@recommend_blue.route('/delete_review', methods=['POST'])
def delete_review():
    """
    删除评价接口
    功能：根据评价ID删除指定的评价
    :param sentence_id: 评价ID
    """
    data = request.json
    sentence_id = data.get('sentence_id')
    # 添加参数校验
    if not sentence_id:
        return jsonify({"error": "缺少评价ID参数"}), 400

    result = RecommendationService.delete_review(sentence_id)
    if not result["success"]:
        return jsonify({"error": result.get("message", "删除失败")}), 400
    return jsonify({"success": True})


@recommend_blue.route('/toggle_permission', methods=['POST'])
def toggle_review_permission():
    """
    管理员切换用户评价权限接口
    请求参数：
    - target_user: 要操作的用户ID
    - enable: true/false 启用/禁用
    """
    # 验证管理员权限
    if session.get('role') != '管理员':
        return jsonify({"error": "权限不足"}), 403

    data = request.json
    required_fields = ['target_user', 'enable']

    if not all(field in data for field in required_fields):
        return jsonify({"error": "缺少必要参数"}), 400

    try:
        result = RecommendationService.toggle_review_permission(
            target_user_id=data['target_user'],
            enable=data.get('enable')
        )

        if result["success"]:
            return jsonify(result), 200
        return jsonify({"error": result["message"]}), 400

    except Exception as e:
        return jsonify({"error": f"服务器错误: {str(e)}"}), 500