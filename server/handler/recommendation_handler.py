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
    query = data.get('query', '').strip()

    # 检查输入是否为空
    if not query:
        return jsonify({"error": "请输入查询内容"}), 400

    # 调用推荐服务获取结果（包含解析和推荐两个步骤）
    query_result = RecommendationService.get_recommendations(query)
    # 失败返回错误信息
    if not query_result["success"]:
        return jsonify({"error": query_result["message"]}), 400

    # 成功返回推荐结果
    return jsonify({"commend_result": query_result["message"]}), 200


@recommend_blue.route('/review', methods=['POST'])
def submit_review():
    """
    提交评价接口（待开发）
    功能：接收学生对导师的评价数据
    """
    pass