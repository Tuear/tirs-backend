from flask import Blueprint, request, jsonify
from service.recommendation_service import RecommendationService

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
    """
        评价提交接口
        :param review_data: 包含以下字段的字典
            - name: 导师姓名 (必填)
            - university: 学校 (必填)
            - department: 学院/系 (必填)
            - academic: 学术特征 (必填)
            - responsibility: responsibility特征 (必填)
            - character: 人品特征 (必填)
        :return: 提交结果
        """
    data = request.json
    required_fields = ['name', 'university', 'department', 'academic', 'responsibility', 'character']

    if not all(field in data for field in required_fields):
        return jsonify({"error": "缺少必要参数"}), 400

    result = RecommendationService.submit_review(data)

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
    result = RecommendationService.get_all_reviews()
    if not result["success"]:
        return jsonify({"error": result["message"]}), 400
    return jsonify(result)


@recommend_blue.route('/delete_review', methods=['POST'])
def delete_review():
    data = request.json
    sentence_id = data.get('sentence_id')
    # 添加参数校验
    if not sentence_id:
        return jsonify({"error": "缺少评价ID参数"}), 400

    result = RecommendationService.delete_review(sentence_id)
    if not result["success"]:
        return jsonify({"error": result.get("message", "删除失败")}), 400
    return jsonify({"success": True})