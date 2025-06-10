import spacy
import re
import logging
from collections import defaultdict
from spacy.matcher import PhraseMatcher
from spacy.util import filter_spans
from config import Config


# 自然语言解析（NLP）类
class NLPProcessor:
    def __init__(self):
        # 从配置中加载词典
        self.academic_terms = Config.ACADEMIC_TERMS  # 学术特征
        self.personality_terms = Config.PERSONALITY_TERMS  # 性格特征
        self.negation_words = Config.NEGATION_WORDS  # 否定词

        try:
            # 加载中文预训练模型
            self.nlp = spacy.load(Config.NLP_MODEL_NAME)
            # 禁用不支持的组件并添加分句器
            self.nlp.disable_pipes(["parser"])
            self.nlp.add_pipe("sentencizer")

            # 创建短语匹配器，确保多字词准确匹配
            self.matcher = PhraseMatcher(self.nlp.vocab, attr="TEXT")

            # 将学术术语和性格术语添加到匹配器
            academic_patterns = [self.nlp.make_doc(term) for term in self.academic_terms]
            personality_patterns = [self.nlp.make_doc(term) for term in self.personality_terms]

            self.matcher.add("ACADEMIC", academic_patterns)
            self.matcher.add("PERSONALITY", personality_patterns)

            # 添加自定义词典到pipeline
            self._add_custom_patterns()

        except Exception as e:
            # logging.error(f"NLP模型加载失败: {str(e)}")
            print(f"NLP模型加载失败: {str(e)}")
            raise RuntimeError("NLP服务初始化失败")

    def _add_custom_patterns(self):
        """
        添加自定义词典到pipeline
        """
        # 构建自定义词典模式
        custom_patterns = [
                              {"label": "ACADEMIC", "pattern": term} for term in self.academic_terms
                          ] + [
                              {"label": "PERSONALITY", "pattern": term} for term in self.personality_terms
                          ]

        # 添加自定义词典到pipeline
        if "entity_ruler" not in self.nlp.pipe_names:
            ruler = self.nlp.add_pipe("entity_ruler")
        else:
            ruler = self.nlp.get_pipe("entity_ruler")

        ruler.add_patterns(custom_patterns)

    def parse_query(self, text):
        """
        解析用户输入的自然语言查询
        """
        try:
            # 预处理：移除多余空格和特殊字符
            cleaned_text = re.sub(r'\s+', ' ', text).strip()
            if not cleaned_text:
                return {"error": "输入内容不能为空"}, False  # 出错返回错误信息和失败状态

            # 使用SpaCy处理文本
            doc = self.nlp(cleaned_text)

            # 使用短语匹配器识别实体
            matches = self.matcher(doc)
            spans = [doc[start:end] for _, start, end in matches]

            # 创建新的实体列表
            new_ents = []
            for span in spans:
                # 检查标签类型（学术或性格）
                label = "ACADEMIC" if span.text in self.academic_terms else "PERSONALITY"
                new_ent = spacy.tokens.Span(doc, span.start, span.end, label=label)
                new_ents.append(new_ent)

            # 合并原始实体和新增实体，并过滤重叠
            filtered_ents = filter_spans(list(doc.ents) + new_ents)
            doc.ents = filtered_ents

            # 提取特征
            features = {
                "academic": self._extract_academic_features(doc),  # 提取学术特征
                "personality": self._extract_personality_features(doc),  # 提取性格特征
                "negations": self._detect_negations(doc)  # 检测否定表达
            }

            return features, True  # 成功返回特征和成功状态

        except Exception as e:
            # logging.error(f"NLP解析失败: {str(e)}")
            print(f"NLP解析失败: {str(e)}")
            return {"解析失败，请尝试其他表述"}, False  # 出错返回错误信息和失败状态

    def _extract_academic_features(self, doc):
        """
        提取学术相关特征
        """
        academic_features = []
        # 提取自定义学术实体
        academic_features.extend(
            ent.text for ent in doc.ents if ent.label_ == "ACADEMIC"
        )
        return list(set(academic_features))

    def _extract_personality_features(self, doc):
        """
        提取性格/风格相关特征
        """
        personality_features = []
        # 提取自定义性格实体
        personality_features.extend(
            ent.text for ent in doc.ents if ent.label_ == "PERSONALITY"
        )
        return list(set(personality_features))

    def _detect_negations(self, doc):
        """
        检测否定表达
        """
        negations = defaultdict(list)
        for token in doc:
            if token.text in self.negation_words:
                negations[token.text].append(token.i)
        return dict(negations)


# 全局NLP处理器实例
nlp_processor = NLPProcessor()