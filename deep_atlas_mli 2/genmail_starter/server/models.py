# 数据库模型定义
from datetime import datetime
from flask_sqlalchemy import SQLAlchemy

# SQLAlchemy 实例，在 main.py 中与 Flask 应用绑定
db = SQLAlchemy()

class Email(db.Model):
    """邮件表：存储单封邮件及线程、已读状态等信息"""

    id = db.Column(db.Integer, primary_key=True)
    thread_id = db.Column(db.String(36), nullable=False, index=True)  # 线程 ID，同一线程多封邮件共享
    sender = db.Column(db.String(255), nullable=False)  # 发件人邮箱
    recipient = db.Column(db.String(255), nullable=False)  # 收件人邮箱
    subject = db.Column(db.String(255), nullable=False)  # 主题
    body = db.Column(db.Text, nullable=False)  # 正文
    created_at = db.Column(db.DateTime, default=datetime.now)  # 创建时间
    is_read = db.Column(db.Boolean, default=False)  # 是否已读

    def to_dict(self):
        """将 ORM 对象转为 JSON 可序列化的字典"""
        return {
            "id": self.id,
            "thread_id": self.thread_id,
            "sender": self.sender,
            "recipient": self.recipient,
            "subject": self.subject,
            "body": self.body,
            "created_at": self.created_at.isoformat(),
            "is_read": self.is_read
        }
