from service.nlp_service import nlp_processor
from utils.sensitive_filter import SensitiveFilter
from uuid import uuid4
from service.database_service import DatabaseService
import hashlib


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
    def generate_professor_id(name, university, department):
        """
        使用 “姓名+学校+学院” 生成导师唯一ID (SHA256哈希值)
        """
        unique_string = f"{name}_{university}_{department}"
        return hashlib.sha256(unique_string.encode()).hexdigest()

    @staticmethod
    def submit_review(review_data):
        """
        处理评价提交（设计文档用例03）
        """
        # 构建评价语句
        review_sentence = f"{review_data['academic']}，{review_data['responsibility']}，{review_data['character']}"

        # 合并特征文本（按需求可调整格式）
        review_features = f"学术特征:{review_data['academic']}|责任心:{review_data['responsibility']}|人品:{review_data['character']}"

        # 调用本类方法生成唯导师一ID
        tutor_id = RecommendationService.generate_professor_id(
            review_data['name'],
            review_data['university'],
            review_data['department']
        )
        tutor_id = f"tutor_{str(tutor_id)}"

        # 生成唯一评价语句ID
        sentence_id = f"sentence_{str(uuid4()).replace('-', '')}"

        # 生成唯一评价特征ID
        txt_id = f"review_{str(uuid4()).replace('-', '')}"

        # 获取数据库服务实例
        professor_db = DatabaseService('professor')

        try:
            # 检查导师是否存在
            existing_professor = professor_db.professor_exists(tutor_id)

            if not existing_professor:
                # 若无该导师记录则创建新导师记录
                professor_db.create_professor(
                    tutor_id, review_data['name'],
                    review_data['university'],
                    review_data['department']
                )

            # 存储review_sentence到review_sentences表
            professor_db.create_review_sentence(sentence_id, tutor_id, review_sentence)

            # 存储review_features到review_features表
            professor_db.create_review_features(txt_id, sentence_id, review_features)

            return {"success": True, "message": "评价提交成功"}

        except Exception as e:
            return {"success": False, "message": f"数据库写入失败: {str(e)}"}

    @staticmethod
    def show_information(tutor_id):
        """
        信息展示(评价+基本信息) - 适配新表结构
        """
        professor_db = DatabaseService('professor')

        try:
            # 1. 查询导师基本信息
            basic_info = professor_db.execute_query(
                "SELECT tutor_id, name, university, department "
                "FROM professor WHERE tutor_id = ?",
                (tutor_id,),
                fetch_one=True
            )

            if not basic_info:
                return {"success": False, "message": "未找到该导师基本信息"}

            # 2. 查询导师的所有评价语句
            review_sentences = professor_db.execute_query(
                "SELECT s.review_sentence "
                "FROM review_sentences s "
                "WHERE s.tutor_id = ?",
                (tutor_id,),
            )

            # 3. 查询导师的所有评价特征（如果需要）
            review_features = professor_db.execute_query(
                "SELECT t.review_features "
                "FROM review_features t "
                "JOIN review_sentences s ON t.sentence_id = s.sentence_id "
                "WHERE s.tutor_id = ?",
                (tutor_id,),
            )

            # 3. 构造返回数据结构
            return {
                "success": True,
                "data": {
                    "tutor_id": basic_info[0],
                    "name": basic_info[1],
                    "university": basic_info[2],
                    "department": basic_info[3],
                    "review_sentences": [s[0] for s in review_sentences] if review_sentences else [],
                    "review_features": [f[0] for f in review_features] if review_features else []
                }
            }

        except Exception as e:
            return {"success": False, "message": f"查询失败: {str(e)}"}
