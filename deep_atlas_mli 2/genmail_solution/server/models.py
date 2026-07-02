from datetime import datetime
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import text

db = SQLAlchemy()


class Email(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    thread_id = db.Column(db.String(36), nullable=False, index=True)
    sender = db.Column(db.String(255), nullable=False)
    recipient = db.Column(db.String(255), nullable=False)
    subject = db.Column(db.String(255), nullable=False)
    body = db.Column(db.Text, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.now)
    is_read = db.Column(db.Boolean, default=False)

    def to_dict(self):
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


class Task(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    description = db.Column(db.Text, nullable=False)
    email_id = db.Column(db.Integer, db.ForeignKey('email.id'), nullable=False)
    thread_id = db.Column(db.String(36), nullable=False, index=True)
    priority = db.Column(db.String(10), default="medium")
    completed = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=datetime.now)

    email = db.relationship('Email', backref='tasks')

    def to_dict(self):
        return {
            "id": self.id,
            "description": self.description,
            "email_id": self.email_id,
            "thread_id": self.thread_id,
            "priority": self.priority,
            "completed": self.completed,
            "created_at": self.created_at.isoformat()
        }


class AgentLog(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    agent_name = db.Column(db.String(100), nullable=False, index=True)
    operation = db.Column(db.String(100), nullable=False)
    model = db.Column(db.String(50), nullable=False)
    input_tokens = db.Column(db.Integer, nullable=False)
    output_tokens = db.Column(db.Integer, nullable=False)
    total_tokens = db.Column(db.Integer, nullable=False)
    cost_usd = db.Column(db.Float, nullable=False)
    latency_ms = db.Column(db.Integer, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.now, index=True)

    def to_dict(self):
        return {
            "id": self.id,
            "agent_name": self.agent_name,
            "operation": self.operation,
            "model": self.model,
            "input_tokens": self.input_tokens,
            "output_tokens": self.output_tokens,
            "total_tokens": self.total_tokens,
            "cost_usd": self.cost_usd,
            "latency_ms": self.latency_ms,
            "created_at": self.created_at.isoformat()
        }


def init_fts(session):
    session.execute(text("""
        CREATE VIRTUAL TABLE IF NOT EXISTS email_fts USING fts5(
            subject, body,
            content='email',
            content_rowid='id'
        )
    """))

    session.execute(text("""
        CREATE TRIGGER IF NOT EXISTS email_fts_insert AFTER INSERT ON email BEGIN
            INSERT INTO email_fts(rowid, subject, body)
            VALUES (new.id, new.subject, new.body);
        END
    """))

    session.execute(text("""
        CREATE TRIGGER IF NOT EXISTS email_fts_update AFTER UPDATE ON email BEGIN
            UPDATE email_fts SET subject = new.subject, body = new.body
            WHERE rowid = old.id;
        END
    """))

    session.execute(text("""
        CREATE TRIGGER IF NOT EXISTS email_fts_delete AFTER DELETE ON email BEGIN
            DELETE FROM email_fts WHERE rowid = old.id;
        END
    """))

    session.commit()


def rebuild_fts(session):
    session.execute(text("DELETE FROM email_fts"))
    session.execute(text("""
        INSERT INTO email_fts(rowid, subject, body)
        SELECT id, subject, body FROM email
    """))
    session.commit()
