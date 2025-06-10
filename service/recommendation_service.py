from service.nlp_service import nlp_processor
from utils.sensitive_filter import SensitiveFilter
from uuid import uuid4
from service.database_service import DatabaseService


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
        处理评价提交（设计文档用例03）
        """
        # 生成唯一ID（UUID4去除连字符）
        tutor_id = f"tutor_{str(uuid4()).replace('-', '')}"

        # 构建评价语句
        review_sentence = f"{review_data['academic']}，{review_data['responsibility']}，{review_data['character']}"

        # 合并特征文本（按需求可调整格式）
        review_txt = f"学术特征:{review_data['academic']}|责任心:{review_data['responsibility']}|人品:{review_data['character']}"

        # 获取数据库服务实例
        professor_db = DatabaseService('professor')

        try:
            professor_db.create_professor(
                tutor_id=tutor_id,
                name=review_data['name'],
                university=review_data['school'],
                department=review_data['academy'],
                review_sentence=review_sentence,
                review_txt=review_txt
            )
            return {"success": True, "message": "评价提交成功"}
        except Exception as e:
            return {"success": False, "message": f"数据库写入失败: {str(e)}"}

    @staticmethod
    def show_information(tutor_id):
        """
        信息展示(评价+基本信息)
        """
        professor_db = DatabaseService('professor')

        try:
            # 查询数据库（明确指定需要返回的字段）
            result = professor_db.execute_query(
                "SELECT tutor_id, name, university, department, review_sentence "
                "FROM professor WHERE tutor_id = ?",
                (tutor_id,),
                fetch_one=True
            )

            if not result:
                return {"success": False, "message": "未找到该导师信息"}

            # 构造返回数据结构
            return {
                "success": True,
                "data": {
                    "tutor_id": result[0],
                    "name": result[1],
                    "university": result[2],
                    "department": result[3],
                    "review_sentence": result[4]
                }
            }

        except Exception as e:
            return {"success": False, "message": f"查询失败: {str(e)}"}
