import sqlite3
import json
from contextlib import closing
from config import Config
from utils.password_utils import hash_password  # 导入密码加密工具


# 多数据库服务类
class DatabaseService:
    def __init__(self, db_type):
        """
        根据类型创建数据库连接
        :param db_type: 'user'/'professor'/'review'
        """
        self.db_type = db_type  # 从参数获取数据库类型
        self.db_path = self._get_db_path()  # 获取数据库路径
        self._init_db()  # 初始化数据库

    def _get_db_path(self):
        """
        获取对应类型的数据库路径
        """
        paths = {
            'user': Config.USER_DB_PATH,
            'professor': Config.PROFESSOR_DB_PATH
        }
        return paths.get(self.db_type, Config.USER_DB_PATH)

    def _init_db(self):
        """
        初始化数据库表结构（设计文档2.4.2）
        """
        with closing(self._get_connection()) as conn:
            cursor = conn.cursor()

            # 用户数据库初始化
            if self.db_type == 'user':
                # 用户表
                cursor.execute('''
                CREATE TABLE IF NOT EXISTS user (
                    user_id TEXT PRIMARY KEY,
                    hashed_password TEXT NOT NULL,
                    role TEXT CHECK(role IN ('学生', '管理员')) DEFAULT '学生',
                    register_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )''')

                # 管理员表
                cursor.execute('''
                CREATE TABLE IF NOT EXISTS admin (
                    admin_id TEXT PRIMARY KEY,
                    admin_name TEXT NOT NULL,
                    password TEXT NOT NULL,
                    rights TEXT DEFAULT '普通管理员'
                )''')

                # 插入初始管理员账户（设计文档1.5）
                cursor.execute('''
                INSERT OR IGNORE INTO admin (admin_id, admin_name, password) 
                VALUES (?, ?, ?)
                ''', (
                    'admin_super',
                    '超级管理员',
                    hash_password('admin123')  # 需要从utils导入
                ))

            # 导师数据库初始化（待实现）
            elif self.db_type == 'professor':
                cursor.execute('''
                CREATE TABLE IF NOT EXISTS professor (
                    tutor_id TEXT PRIMARY KEY,
                    name TEXT NOT NULL,
                    university TEXT,
                    department TEXT,
                    review_sentence TEXT,
                    review_txt TEXT
                )''')


            conn.commit()

    def _get_connection(self):
        """
        获取数据库连接
        """
        return sqlite3.connect(self.db_path)

    def execute_query(self, query: str, params: tuple = (), fetch_one: bool = False):
        """
        执行SQL查询
        :param query: SQL语句
        :param params: 参数元组
        :param fetch_one: 是否只获取一条记录
        :return: 查询结果
        """
        with closing(self._get_connection()) as conn:
            cursor = conn.cursor()
            cursor.execute(query, params)
            conn.commit()
            if fetch_one:
                return cursor.fetchone()
            return cursor.fetchall()

    def user_exists(self, user_id: str) -> bool:
        """
        检查用户是否存在（设计文档2.4.2）
        """
        result = self.execute_query(
            "SELECT 1 FROM user WHERE user_id = ?",
            (user_id,),
            fetch_one=True
        )
        return bool(result)

    def admin_exists(self, admin_id: str) -> bool:
        """
        检查管理员是否存在
        """
        result = self.execute_query(
            "SELECT 1 FROM admin WHERE admin_id = ?",
            (admin_id,),
            fetch_one=True
        )
        return bool(result)

    def create_user(self, user_id: str, hashed_password: str, role: str = '学生') -> None:
        """
        创建新用户
        """
        self.execute_query(
            "INSERT INTO user (user_id, hashed_password, role) VALUES (?, ?, ?)",
            (user_id, hashed_password, role)
        )

    def get_user(self, user_id: str) -> dict:
        """
        获取用户信息
        """
        result = self.execute_query(
            "SELECT * FROM user WHERE user_id = ?",
            (user_id,),
            fetch_one=True
        )
        if result:
            return {
                'user_id': result[0],
                'hashed_password': result[1],
                'role': result[2],
                'register_time': result[3]
            }
        return None

    def get_admin(self, admin_id: str) -> dict:
        """
        获取管理员信息
        """
        result = self.execute_query(
            "SELECT * FROM admin WHERE admin_id = ?",
            (admin_id,),
            fetch_one=True
        )
        if result:
            return {
                'admin_id': result[0],
                'admin_name': result[1],
                'password': result[2],
                'rights': result[3]
            }
        return None

    def create_professor(self, tutor_id: str, name: str, university: str, department: str,
                         review_sentence: str, review_txt: str) -> None:
        """
        创建新导师记录
        """
        self.execute_query(
            "INSERT INTO professor (tutor_id, name, university, department, review_sentence, review_txt) "
            "VALUES (?, ?, ?, ?, ?, ?)",
            (tutor_id, name, university, department, review_sentence, review_txt)
        )