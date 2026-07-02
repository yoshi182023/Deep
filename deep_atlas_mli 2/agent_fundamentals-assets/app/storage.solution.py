import sqlite3  # 导入 SQLite 数据库驱动，用于本地持久化开支数据
from datetime import datetime  # 导入日期时间模块，用于生成默认日期
from typing import List, Dict, Optional  # 导入类型注解：列表、字典、可选值
import json  
class ExpenseStorage:  # 开支存储类：封装所有与 SQLite 交互的 CRUD 操作
    def __init__(self, db_path: str = "expenses.db"):  
        self.db_path = db_path  # 保存数据库路径到实例属性
        self._init_db()   # 初始化时自动建表（若表不存在则创建）
    def _init_db(self):  
        with sqlite3.connect(self.db_path) as conn:  
            conn.execute(   
                """
                CREATE TABLE IF NOT EXISTS expenses (  # 若表不存在则创建 expenses 表
                    id INTEGER PRIMARY KEY AUTOINCREMENT,  # 主键，自增整数
                    category TEXT NOT NULL,  # 开支分类，必填（如 groceries、dining）
                    amount REAL NOT NULL,  # 金额，必填，浮点数
                    description TEXT,  # 可选描述
                    date TEXT NOT NULL  # 日期，必填，格式 YYYY-MM-DD
                )
            """
            )   
    def add_expense(   
        self, category: str, amount: float, description: str = "", date: str = None
    ) -> Dict:  # 返回包含 id 及字段值的字典
        if date is None:  # 若调用方未传日期
            date = datetime.now().strftime("%Y-%m-%d")  
        with sqlite3.connect(self.db_path) as conn:  # 打开数据库连接
            cursor = conn.execute(  # 执行参数化 INSERT，防止 SQL 注入
                "INSERT INTO expenses (category, amount, description, date) VALUES (?, ?, ?, ?)",  # ? 为占位符
                (category, amount, description, date),  # 按顺序绑定四个参数值
            )
            return {   
                "id": cursor.lastrowid,   
                "category": category,  
                "amount": amount,  
                "description": description,   
                "date": date,   
            }
    def get_expenses(  # 查询开支列表，支持可选筛选条件（动态 WHERE）
        self,
        category: Optional[str] = None,   
        start_date: Optional[str] = None,   
        end_date: Optional[str] = None,  
    ) -> List[Dict]:  # 返回字典列表，每条对应一行开支
        query = "SELECT id, category, amount, description, date FROM expenses WHERE 1=1"  # 基础查询，1=1 便于后续拼接 AND
        params = []  # 参数列表，与 SQL 中的 ? 占位符一一对应
        if category:  # 若传了分类
            query += " AND category = ?"  # 动态追加分类条件
            params.append(category)  # 把分类值加入参数列表
        if start_date:  # 若传了起始日期
            query += " AND date >= ?"  # 动态追加日期下限
            params.append(start_date)  # 加入起始日期参数
        if end_date:  # 若传了结束日期
            query += " AND date <= ?"  # 动态追加日期上限
            params.append(end_date)  # 加入结束日期参数

        with sqlite3.connect(self.db_path) as conn:  # 连接数据库
            cursor = conn.execute(query, params)  # 执行动态拼接后的查询
            return [  # 将每一行转为字典
                {
                    "id": row[0],  # 第 0 列：id
                    "category": row[1],  # 第 1 列：category
                    "amount": row[2],  # 第 2 列：amount
                    "description": row[3],  # 第 3 列：description
                    "date": row[4],  # 第 4 列：date
                }
                for row in cursor.fetchall()  # 遍历查询结果的所有行
            ]
    def update_expense(  # 按 id 更新开支，只更新传入的非 None 字段
        self,
        expense_id: int,  # 要更新的记录 id
        category: str = None,  # 新分类（可选）
        amount: float = None,  # 新金额（可选）
        description: str = None,  # 新描述（可选）
        date: str = None,  # 新日期（可选）
    ) -> Dict:  # 返回更新后的完整记录
        updates = []  # 存放 SET 子句片段，如 "category = ?"
        params = []  # 存放 SET 对应的参数值

        if category is not None:  # 若提供了新分类
            updates.append("category = ?")  # 加入更新片段
            params.append(category)  # 加入对应参数
        if amount is not None:  # 若提供了新金额
            updates.append("amount = ?")
            params.append(amount)
        if description is not None:  # 若提供了新描述
            updates.append("description = ?")
            params.append(description)
        if date is not None:   
            updates.append("date = ?")
            params.append(date)
        if not updates:  
            raise ValueError("No fields to update")  
        params.append(expense_id)  
        with sqlite3.connect(self.db_path) as conn:  
            conn.execute(   
                f"UPDATE expenses SET {', '.join(updates)} WHERE id = ?", params  # SET 部分动态拼接；id 用占位符
            )
            cursor = conn.execute(   
                "SELECT id, category, amount, description, date FROM expenses WHERE id = ?",
                (expense_id,),   
            )
            row = cursor.fetchone()  
            if row:   
                return {   
                    "id": row[0],
                    "category": row[1],
                    "amount": row[2],
                    "description": row[3],
                    "date": row[4],
                }
            raise ValueError(f"Expense {expense_id} not found") 
    def delete_expense(self, expense_id: int) -> Dict:  
        with sqlite3.connect(self.db_path) as conn:   
            cursor = conn.execute(  
                "SELECT id, category, amount, description, date FROM expenses WHERE id = ?",
                (expense_id,),
            )
            row = cursor.fetchone()  
            if not row:   
                raise ValueError(f"Expense {expense_id} not found") 
            conn.execute("DELETE FROM expenses WHERE id = ?", (expense_id,))  
            return {   
                "id": row[0],
                "category": row[1],
                "amount": row[2],
                "description": row[3],
                "date": row[4],
            }
