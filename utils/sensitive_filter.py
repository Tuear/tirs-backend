from config import Config


# 敏感词过滤器
class SensitiveFilter:
    @classmethod
    def check(cls, text):
        """
        检查文本是否包含敏感词
        """
        if not text:
            return False

        # 从配置中获取敏感词列表
        sensitive_words = Config.SENSITIVE_WORDS

        lower_text = text.lower()
        for word in sensitive_words:
            if word.lower() in lower_text:
                return True
        return False