from service.database_service import DatabaseService
from utils.password_utils import hash_password, verify_password
from flask import session
from config import Config

# 启动用户数据库服务
user_db = DatabaseService('user')


# 认证服务类
class AuthService:
    @staticmethod
    def register_user(user_id: str, password: str):
        """
        用户注册（设计文档用例01）
        """
        # 验证用户ID格式
        if not AuthService._validate_user_id(user_id):
            return {"success": False, "message": "无效的用户ID格式"}

        # 检查用户是否已存在
        if user_db.user_exists(user_id):
            return {"success": False, "message": "该用户ID已注册"}

        # 验证密码强度
        if len(password) < 6:
            return {"success": False, "message": "密码长度至少6位"}

        # 加密密码
        hashed_pw = hash_password(password)

        # 创建用户
        user_db.create_user(user_id, hashed_pw)

        return {"success": True, "message": "注册成功"}

    @staticmethod
    def login_user(user_id: str, password: str):
        """
        用户登录（设计文档用例01）
        """
        # 验证用户ID格式
        if not AuthService._validate_user_id(user_id):
            return {"success": False, "message": "无效的用户ID格式"}

        # 获取用户数据
        user_data = user_db.get_user(user_id)
        if not user_data:
            return {"success": False, "message": "用户不存在"}

        # 验证密码
        if not verify_password(password, user_data['hashed_password']):
            return {"success": False, "message": "密码错误"}

        # 设置session
        session['user_id'] = user_id
        session['role'] = user_data['role']
        session['logged_in'] = True

        return {"success": True, "role": user_data['role'], "message": "登录成功"}

    @staticmethod
    def login_admin(admin_id: str, password: str):
        """
        管理员登录（设计文档用例01）
        """
        # 必须是管理员ID格式
        if not admin_id.startswith(Config.ADMIN_ID_PREFIX):
            return {"success": False, "message": "无效的管理员ID"}

        # 获取管理员数据
        admin_data = user_db.get_admin(admin_id)
        if not admin_data:
            return {"success": False, "message": "管理员不存在"}

        # 验证密码
        if not verify_password(password, admin_data['password']):
            return {"success": False, "message": "密码错误"}

        # 设置session
        session['admin_id'] = admin_id
        session['role'] = '管理员'
        session['logged_in'] = True

        return {"success": True, "role": "管理员", "message": "管理员登录成功"}

    @staticmethod
    def logout():
        """
        退出登录
        """
        session.clear()
        return {"success": True, "message": "已退出登录"}

    @staticmethod
    def _validate_user_id(user_id: str) -> bool:
        """
        验证用户ID格式（邮箱格式严格验证）
        规则：
        1. 必须包含且仅包含一个@符号
        2. @符号不能是首位或末位字符
        3. @符号后有且至少有一个点号(.)
        4. 最后一个点号后必须有内容（顶级域名）
        5. 点号不能直接出现在@符号后面（防止@.开头）
        6. 邮箱长度至少6个字符
        """
        # 检查长度基础要求
        if len(user_id) < 6:
            return False

        # 检查必须包含且仅包含一个@符号
        if user_id.count('@') != 1:
            return False

        # 分割本地部分和域名
        local_part, domain = user_id.split('@')

        # 检查本地部分和域名非空
        if not local_part or not domain:
            return False

        # 检查域名中必须包含点号
        if '.' not in domain:
            return False

        # 检查点号位置有效性
        last_dot_index = domain.rfind('.')
        if (last_dot_index == -1 or  # 确保有实际点号位置
                last_dot_index == 0 or  # 防止类似"@.com"
                last_dot_index == len(domain) - 1 or  # 防止末尾点号（如"@domain."）
                domain.startswith('.')):  # 防止点号开头（如"@.domain.com"）
            return False

        # 所有检查通过
        return True
