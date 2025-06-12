from service.nlp_service import nlp_processor
from utils.sensitive_filter import SensitiveFilter
from uuid import uuid4
from service.database_service import DatabaseService
import hashlib
from config import Config


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
    def get_recommendations(text, university, department):
        """
        获取推荐结果（实现完整推荐逻辑）
        :param text: 用户查询文本
        :param university: 用户选择的学校
        :param department: 用户选择的学院
        """
        query_result = RecommendationService.parse_query(text)
        if not query_result["success"]:
            return {"success": False, "message": query_result["message"]}

        NLP_result = query_result["message"]
        print(f"用户输入语义解析结果为{NLP_result}")

        # 获取积极特征
        positive_features = query_result["message"]["positive"]
        academic_features = positive_features["academic"]
        personality_features = positive_features["personality"]

        # 合并“responsibility”和“人品”到性格特征
        combined_personality_features = personality_features

        # 获取所有符合条件的导师ID
        professor_db = DatabaseService('professor')
        if university == "全部" and department == "全部":
            tutor_ids = [row[0] for row in professor_db.execute_query(
                "SELECT tutor_id FROM professor"
            )]
        else:
            tutor_ids = [row[0] for row in professor_db.execute_query(
                "SELECT tutor_id FROM professor WHERE university = ? AND department = ?",
                (university, department)
            )]

        tutor_scores = []
        for tutor_id in tutor_ids:
            # 获取导师信息和特征
            tutor_info = RecommendationService.show_information(tutor_id)
            if not tutor_info["success"]:
                continue

            review_features = tutor_info["data"]["review_features"]
            tutor_academic_features = []
            tutor_personality_features = []
            for feature_str in review_features:
                parts = feature_str.split('|')
                for part in parts:
                    if part.startswith("学术特征:"):
                        tutor_academic_features.extend(part[5:].split("，"))
                    elif part.startswith("responsibility:") or part.startswith("人品:"):
                        tutor_personality_features.extend(part.split(":")[1].split("，"))

            # 计算学术特征匹配分数
            academic_matches = len(set(academic_features) & set(tutor_academic_features))
            print(f"学术特征匹配数量: {academic_matches}")
            academic_score = (academic_matches / len(academic_features)) * int(Config.ACADEMIC_WEIGHT) if academic_features else 0

            # 计算性格特征匹配分数
            personality_matches = len(set(combined_personality_features) & set(tutor_personality_features))
            print(f"性格特征匹配数量: {personality_matches}")
            personality_score = (personality_matches / len(combined_personality_features)) * int(Config.PERSONALITY_WEIGHT) if combined_personality_features else 0

            # 计算综合分数
            total_score = academic_score + personality_score

            # 将匹配度分数添加到导师信息中
            tutor_data = tutor_info["data"]
            tutor_data["match_score"] = total_score
            tutor_scores.append((tutor_data, total_score))

        # 按综合分数从高到低排序
        tutor_scores.sort(key=lambda x: x[1], reverse=True)

        # 取前5个导师
        top_5_tutors = [tutor[0] for tutor in tutor_scores[:5]]

        # 处理0分导师数据结构
        processed_tutors = []
        for tutor in top_5_tutors:
            if tutor["match_score"] == 0:
                # 创建带提示信息的空数据结构
                processed_tutors.append({
                    "department": "",
                    "match_score": 0,
                    "name": "",
                    "review_features": [],
                    "review_sentences": [],
                    "tutor_id": "",
                    "university": "",
                    "notice": "以下导师不符合您的要求，可以试试重新调整要求。"
                })
            else:
                processed_tutors.append(tutor)

        return {"success": True, "message": processed_tutors}


    @staticmethod
    def generate_professor_id(name, university, department):
        """
        使用 “姓名+学校+学院” 生成导师唯一ID (SHA256哈希值)
        """
        unique_string = f"{name}_{university}_{department}"
        return hashlib.sha256(unique_string.encode()).hexdigest()

    @staticmethod
    def submit_review(review_data, user_id):
        """
        处理评价提交（设计文档用例03）
        """
        # 构建评价语句
        review_sentence = f"{review_data['academic']}，{review_data['responsibility']}，{review_data['character']}"

        # 检查评价内容是否合规
        if SensitiveFilter.check(review_sentence):
            return {"success": False, "message": "评价内容不合规！请重新填写评价内容。"}

        # 合并特征文本（按需求可调整格式）
        review_features = f"学术特征:{review_data['academic']}|responsibility:{review_data['responsibility']}|人品:{review_data['character']}"

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
        feature_id = f"review_{str(uuid4()).replace('-', '')}"

        # 获取数据库服务实例
        professor_db = DatabaseService('professor')

        try:
            # 检查导师是否存在
            existing_professor = professor_db.professor_exists(tutor_id)

            if not existing_professor:
                # 若无该导师记录则创建新导师记录
                professor_db.create_professor(
                    tutor_id,
                    review_data['name'],
                    review_data['university'],
                    review_data['department']
                )

            # 存储review_sentence到review_sentences表
            professor_db.create_review_sentence(sentence_id, tutor_id, user_id, review_sentence)

            # 存储review_features到review_features表
            professor_db.create_review_features(feature_id, sentence_id, review_features)

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

    @staticmethod
    def get_all_reviews():
        """获取所有导师评价信息"""
        professor_db = DatabaseService('professor')
        try:
            # 获取所有评价语句及关联特征
            reviews = professor_db.execute_query('''
                SELECT s.sentence_id, p.tutor_id, p.name, p.university, p.department, 
                       s.review_sentence, t.review_features, s.user_id
                FROM review_sentences s
                JOIN professor p ON s.tutor_id = p.tutor_id
                LEFT JOIN review_features t ON s.sentence_id = t.sentence_id
            ''')

            # 定义字段索引映射
            FIELD_MAPPING = {
                'sentence_id': 0,
                'tutor_id': 1,
                'name': 2,
                'university': 3,
                'department': 4,
                'review_sentence': 5,
                'review_features': 6,
                'user_id': 7
            }

            return {
                "success": True,
                "data": [{
                    "sentence_id": row[FIELD_MAPPING['sentence_id']],
                    "tutor_id": row[FIELD_MAPPING['tutor_id']],
                    "name": row[FIELD_MAPPING['name']],
                    "university": row[FIELD_MAPPING['university']],
                    "department": row[FIELD_MAPPING['department']],
                    "review_sentence": row[FIELD_MAPPING['review_sentence']],
                    "review_features": row[FIELD_MAPPING['review_features']],
                    "user_id": row[FIELD_MAPPING['user_id']]
                } for row in reviews]
            }

        except Exception as e:
            return {"success": False, "message": f"查询失败: {str(e)}"}

    @staticmethod
    def delete_review(sentence_id):
        professor_db = DatabaseService('professor')
        try:
            professor_db.execute_update(sentence_id)
            return {"success": True}
        except Exception as e:
            return {"success": False, "message": f"删除失败: {str(e)}"}