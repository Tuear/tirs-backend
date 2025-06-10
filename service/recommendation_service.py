from service.nlp_service import nlp_processor
from utils.sensitive_filter import SensitiveFilter


# 推荐引擎类
class RecommendationService:
    @staticmethod
    def parse_query(text):
        """
        解析用户查询（设计文档用例02）
        """
        # 调用NLP服务解析查询
        answer, success = nlp_processor.parse_query(text)
        # 失败返回错误信息
        if not success:
            return {"success": False, "message": answer}

        # 成功返回解析得到的特征
        else:
            return {"success": True, "message": answer}

    @staticmethod
    def get_recommendations(text):
        """
        获取推荐结果（占位，待实现完整）
        """
        query_result = RecommendationService.parse_query(text)  # 获取语义解析结果
        # 失败返回错误信息
        if not query_result["success"]:
            return {"success": False, "message": query_result["message"]}

        # 成功返回推荐结果
        # """
        # 推荐功能待开发实现，现阶段先返回语义解析结果
        # """
        else:
            return {"success": True, "message": query_result["message"]}

    @staticmethod
    def submit_review(review_data):
        """
        提交评价（待完整实现）
        """
        pass